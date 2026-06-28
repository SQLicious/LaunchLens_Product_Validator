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
from langgraph.prebuilt import ToolNode, tools_condition

from . import nodes, router
from .state import State
from .tools import ALL_TOOLS


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

    # CONCEPT 4: agent <-> tools loop
    g.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: "verdict"})
    g.add_edge("tools", "agent")
    g.add_edge("verdict", END)

    return g.compile(checkpointer=checkpointer)
