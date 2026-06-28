"""CONCEPT 3 (Routing): classify the founder's intent, then branch.

`classify_intent` is a node that inspects the latest user message and sets
state["intent"]. It also resets `research` ([]) so each turn starts clean.
`route` is the conditional-edge function: it returns the next node name(s).
For a full launch report it returns a LIST of three node names, which is how we
trigger the fan-out (parallel) branch.

Keyword routing is used on purpose: it is cheap, deterministic, fully
explainable, and saves an LLM call. Swap in an LLM classifier if you prefer.
"""
from __future__ import annotations

from .state import State

_FULL = ["worth launching", "should i launch", "go or no", "launch", "verdict",
         "assess", "evaluate", "is it worth", "should we launch", "viable"]
_PRICING = ["price", "pricing", "cost", "cheap", "expensive", "margin",
            "how much", "undercut"]
_DEMAND = ["trend", "trending", "demand", "search volume", "interest",
           "popular", "growing", "rising"]


def _latest_user_raw(state: State) -> str:
    """The latest human message, original casing preserved."""
    for msg in reversed(state.get("messages", [])):
        if getattr(msg, "type", None) == "human":
            return msg.content or ""
    return ""


def _latest_user_text(state: State) -> str:
    return _latest_user_raw(state).lower()


def derive_search_query(text: str) -> str:
    """Distil a short product search keyword from a founder's message.

    Search engines want a topic, not a paragraph -- Google Trends in particular
    rejects queries over ~100 characters. Short messages are used as-is; longer
    ones are reduced to a 2-5 word keyword via the LLM, with a plain-truncation
    fallback so search never hard-fails (and so MOCK mode needs no LLM key).
    """
    text = (text or "").strip()
    if len(text) <= 60:
        return text

    from . import config
    if config.MOCK_MODE:
        return text[:80]
    try:
        prompt = (
            "Extract a short product search keyword (2-5 words, no price, no "
            "punctuation) describing the product in this founder message. "
            "Return ONLY the keyword, nothing else.\n\n"
            f"{text}"
        )
        keyword = config.get_llm().invoke(prompt).content.strip().strip('"')
        keyword = keyword.splitlines()[0].strip()[:80]
        return keyword or text[:80]
    except Exception:
        return text[:80]


def classify_intent(state: State) -> dict:
    """Router node: set intent, distil a search query, clear last turn's research."""
    text = _latest_user_text(state)
    if any(k in text for k in _FULL):
        intent = "full"
    elif any(k in text for k in _PRICING):
        intent = "pricing"
    elif any(k in text for k in _DEMAND):
        intent = "demand"
    else:
        intent = "chat"
    # only spend an LLM call when a branch will actually search
    query = "" if intent == "chat" else derive_search_query(_latest_user_raw(state))
    return {"intent": intent, "research": [], "query": query}  # [] resets the reducer


def route(state: State):
    """Conditional edge: map intent -> next node(s).

    Returning a list ("full" case) fans out to three parallel nodes.
    """
    intent = state.get("intent", "chat")
    if intent == "full":
        return ["fan_trends", "fan_amazon", "fan_news"]
    return intent  # "demand" | "pricing" | "chat"
