"""Graph nodes: summarization (memory), fan-out branches, the agent, the verdict.

CONCEPT 4 (Agent + tools): `agent_node` is an LLM bound to all SerpApi/Oxylabs
tools; the agent<->tools loop is wired in graph.py via tools_condition.
CONCEPT 5 (Short-term memory): `summarize_node` compresses old messages once the
chat gets long, preserving key facts and never breaking tool-call sequences.
The fan-out branch nodes (CONCEPT 2) pre-fetch demand+supply in parallel.
"""
from __future__ import annotations

import json

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage, SystemMessage

from . import config
from .state import State
from .tools import ALL_TOOLS
from .tools.serpapi_tools import fetch_news, fetch_shopping, fetch_trends
from .tools.oxylabs_tools import fetch_amazon_search

SYSTEM_PROMPT = SystemMessage(content=(
    "You are LaunchLens, a market-intelligence copilot for founders. "
    "Your job is to FUSE demand signals (Google: Trends, Shopping, News) with "
    "supply signals (Amazon via Oxylabs: listings, prices, review complaints) "
    "into ONE combined judgement -- never two separate reports. "
    "When you have enough evidence, end your answer with a clear verdict line "
    "formatted exactly as 'VERDICT: Go' or 'VERDICT: No-Go' or 'VERDICT: Niche', "
    "followed by a 2-3 sentence rationale covering demand, a price band, and "
    "positioning/differentiation. Call tools when you need fresh data."
))


def _latest_user_text(state: State) -> str:
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, HumanMessage):
            return msg.content or ""
    return ""


# ---------- CONCEPT 5: short-term memory (summarization) ----------

def summarize_node(state: State) -> dict:
    """Compress the conversation once it grows past SUMMARY_TRIGGER messages.

    Only plain Human/AI text messages are removed -- tool calls and their
    ToolMessage results are left intact so the agent<->tools history never breaks.
    The last 4 messages are always kept verbatim for immediate context.
    """
    msgs = state.get("messages", [])
    if len(msgs) <= config.SUMMARY_TRIGGER:
        return {}

    removable = []
    for m in msgs[:-4]:
        if isinstance(m, HumanMessage):
            removable.append(m)
        elif isinstance(m, AIMessage) and not m.tool_calls:
            removable.append(m)
    if not removable:
        return {}

    transcript = "\n".join(f"{m.type}: {m.content}" for m in removable if m.content)
    prompt = (
        f"Running summary so far:\n{state.get('summary', '(none)')}\n\n"
        f"New conversation to fold in:\n{transcript}\n\n"
        "Return an updated, concise summary. Preserve product ideas, target "
        "markets, target prices, key findings, and any verdicts already given."
    )
    new_summary = config.get_llm().invoke(prompt).content
    removals = [RemoveMessage(id=m.id) for m in removable]
    return {"summary": new_summary, "messages": removals}


# ---------- CONCEPT 2: fan-out branch nodes (run in parallel) ----------

def trends_node(state: State) -> dict:
    """Parallel branch: pull Google Trends demand."""
    q = _latest_user_text(state)
    return {"research": [{"source": "google_trends", "data": fetch_trends(q)}]}


def amazon_node(state: State) -> dict:
    """Parallel branch: pull Amazon supply (Oxylabs)."""
    q = _latest_user_text(state)
    return {"research": [{"source": "amazon_search", "data": fetch_amazon_search(q)}]}


def news_node(state: State) -> dict:
    """Parallel branch: pull Google News landscape."""
    q = _latest_user_text(state)
    return {"research": [{"source": "google_news", "data": fetch_news(q)}]}


# ---------- single-source branch nodes (routing targets) ----------

def demand_node(state: State) -> dict:
    """Demand-only branch (Google Trends)."""
    q = _latest_user_text(state)
    return {"research": [{"source": "google_trends", "data": fetch_trends(q)}]}


def pricing_node(state: State) -> dict:
    """Pricing branch: Google Shopping + Amazon, the two price worlds."""
    q = _latest_user_text(state)
    return {"research": [
        {"source": "google_shopping", "data": fetch_shopping(q)},
        {"source": "amazon_search", "data": fetch_amazon_search(q)},
    ]}


# ---------- CONCEPT 4: the agent ----------

def agent_node(state: State) -> dict:
    """LLM agent. Sees the summary + any pre-fetched research, and can call tools."""
    llm = config.get_llm(ALL_TOOLS)
    context_blocks = []
    if state.get("summary"):
        context_blocks.append(f"Conversation summary:\n{state['summary']}")
    if state.get("research"):
        # slim, bounded context -- never dump unbounded scrape into the prompt
        evidence = json.dumps(state["research"])[:4000]
        context_blocks.append(f"Evidence gathered this turn (demand + supply):\n{evidence}")

    messages = [SYSTEM_PROMPT]
    if context_blocks:
        messages.append(SystemMessage(content="\n\n".join(context_blocks)))
    messages += state.get("messages", [])

    return {"messages": [llm.invoke(messages)]}


def verdict_node(state: State) -> dict:
    """Extract the Go / No-Go / Niche label from the agent's final answer."""
    last = ""
    for m in reversed(state.get("messages", [])):
        if isinstance(m, AIMessage) and m.content:
            last = m.content.upper()
            break
    if "NO-GO" in last or "NO GO" in last:
        label = "No-Go"
    elif "NICHE" in last:
        label = "Niche"
    elif "GO" in last:
        label = "Go"
    else:
        label = "Undecided"
    return {"verdict": label}
