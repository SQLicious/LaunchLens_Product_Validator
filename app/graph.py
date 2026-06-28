r"""CONCEPT 1 (Graph construction): wire every node into one typed StateGraph.

Flow:
    START
      -> summarize        (CONCEPT 5 applied: short-term memory / summarization)
      -> router           (CONCEPT 3 applied: routing, conditional edges)
         |- demand  -----------------\
         |- pricing ------------------> agent
         |- chat   -------------------/
         |- full  -> [fan_trends, fan_amazon, fan_news]  (CONCEPT 2: fan-out)
                          \____ all merge into ____/  -> agent
      agent  <-> tools    (CONCEPT 4: agent + tools loop)
      agent  -> verdict -> END

The compiled graph takes a checkpointer (CONCEPT 5) so state is saved after
every node and conversations survive restarts, keyed by thread_id.
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from . import config, nodes, router
from .state import State
from .tools import ALL_TOOLS


def route_agent(state: State) -> str:
    """Deterministic gate for the agent<->tools loop (CONCEPT 4).

    The cap is enforced HERE, in code -- not by asking the model nicely. Continue
    to "tools" only while the agent asked for tools AND fewer than
    config.TOOL_BUDGET tool results have been gathered this turn; otherwise end
    the loop at "verdict". This bounds the number of paid tool/LLM round-trips a
    single founder question can trigger (the runaway loop that drained the free
    quota). agent_node drops the tool bindings once the budget is hit, so the
    agent can't emit a trailing tool_call that this gate would strand without a
    result.
    """
    last = state["messages"][-1]
    wants_tools = bool(getattr(last, "tool_calls", None))
    if wants_tools and nodes.tools_used_this_turn(state) < config.TOOL_BUDGET:
        return "tools"
    return "verdict"


def build_graph(checkpointer=None):
    """Construct and compile the LaunchLens graph."""
    g = StateGraph(State)

    # nodes
    g.add_node("summarize", nodes.summarize_node)
    g.add_node("router", router.classify_intent)
    g.add_node("demand", nodes.demand_node)
    g.add_node("pricing", nodes.pricing_node)
    g.add_node("fan_trends", nodes.trends_node)
    g.add_node("fan_amazon", nodes.amazon_node)
    g.add_node("fan_news", nodes.news_node)
    g.add_node("agent", nodes.agent_node)
    g.add_node("tools", ToolNode(ALL_TOOLS))
    g.add_node("verdict", nodes.verdict_node)

    # edges
    g.add_edge(START, "summarize")
    g.add_edge("summarize", "router")

    # CONCEPT 3: routing -- one path per intent (+ fan-out list for "full")
    g.add_conditional_edges(
        "router",
        router.route,
        {
            "demand": "demand",
            "pricing": "pricing",
            "chat": "agent",
            "fan_trends": "fan_trends",
            "fan_amazon": "fan_amazon",
            "fan_news": "fan_news",
        },
    )

    # branches feed the agent. The three fan-out nodes converge on "agent",
    # which runs once after all of them finish (the merge).
    for n in ("demand", "pricing", "fan_trends", "fan_amazon", "fan_news"):
        g.add_edge(n, "agent")

    # CONCEPT 4: agent <-> tools loop, with a deterministic per-turn tool budget
    # (route_agent) so the loop can never run away and exhaust a paid quota.
    g.add_conditional_edges("agent", route_agent, {"tools": "tools", "verdict": "verdict"})
    g.add_edge("tools", "agent")
    g.add_edge("verdict", END)

    return g.compile(checkpointer=checkpointer)
