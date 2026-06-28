"""Typed graph state + reducers.

CONCEPT 1 (Graph & state): a single typed StateGraph state. Two channels use
reducers so that fan-out (parallel) writes MERGE instead of overwriting:
  - `messages` uses LangGraph's add_messages (append + supports RemoveMessage).
  - `research` uses a custom reducer that accumulates parallel results, with an
    explicit reset signal ([]) emitted by the router at the start of each turn.
"""
from __future__ import annotations

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


def merge_research(existing: list | None, new: list | None) -> list:
    """Reducer for fan-out results.

    - `[]` is a reset signal (router clears last turn's research each turn).
    - otherwise the new items are appended to the existing list, so three
      parallel nodes writing in the same superstep all survive.
    """
    if new == []:
        return []
    return (existing or []) + (new or [])


class State(TypedDict, total=False):
    # full conversation; add_messages handles appends and RemoveMessage deletions
    messages: Annotated[list, add_messages]
    # router output: "demand" | "pricing" | "full" | "chat"
    intent: str
    # short product keyword distilled from the founder's message, used as the
    # search query for Trends/News/Shopping/Amazon (raw message is too long)
    query: str
    # demand + supply evidence gathered this turn (merged across parallel nodes)
    research: Annotated[list, merge_research]
    # rolling conversation summary kept by the summarization node
    summary: str
    # final Go / No-Go / Niche label
    verdict: str
    # verdict confidence: High | Medium | Low (Unknown if agent omitted it)
    confidence: str
