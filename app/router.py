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


def _latest_user_text(state: State) -> str:
    for msg in reversed(state.get("messages", [])):
        if getattr(msg, "type", None) == "human":
            return (msg.content or "").lower()
    return ""


def classify_intent(state: State) -> dict:
    """Router node: set intent and clear last turn's research."""
    text = _latest_user_text(state)
    if any(k in text for k in _FULL):
        intent = "full"
    elif any(k in text for k in _PRICING):
        intent = "pricing"
    elif any(k in text for k in _DEMAND):
        intent = "demand"
    else:
        intent = "chat"
    return {"intent": intent, "research": []}  # [] resets the reducer


def route(state: State):
    """Conditional edge: map intent -> next node(s).

    Returning a list ("full" case) fans out to three parallel nodes.
    """
    intent = state.get("intent", "chat")
    if intent == "full":
        return ["fan_trends", "fan_amazon", "fan_news"]
    return intent  # "demand" | "pricing" | "chat"
