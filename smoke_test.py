"""Smoke test: exercises the graph wiring WITHOUT real API keys or a real LLM.

We patch config.get_llm with a fake chat model, run in MOCK_MODE, and assert:
  - routing picks the right branch
  - fan-out runs 3 parallel nodes whose results MERGE (reducer works)
  - the agent->verdict path produces a verdict
  - memory persists across a simulated restart (same thread id, new graph)
"""
import os
os.environ["MOCK_MODE"] = "true"

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver

from app import config
from app.graph import build_graph
from app.router import classify_intent, route


class FakeLLM:
    """Stand-in for ChatOpenAI: no tool calls, canned verdict."""
    def bind_tools(self, tools):
        return self
    def invoke(self, messages):
        return AIMessage(content="Demand is rising and reviews complain about leaks. "
                                 "VERDICT: Go -- launch a leak-proof 1L bottle at INR 1199-1399.")


config.get_llm = lambda tools=None: FakeLLM()

DB = "/tmp/smoke.sqlite"
if os.path.exists(DB):
    os.remove(DB)

print("== 1. Routing ==")
for text, expected in [("is it worth launching a water bottle?", "full"),
                       ("what price should i sell at?", "pricing"),
                       ("is demand trending up?", "demand"),
                       ("hello there", "chat")]:
    st = {"messages": [HumanMessage(text)]}
    out = classify_intent(st)
    r = route({**st, **out})
    assert out["intent"] == expected, f"{text!r} -> {out['intent']} != {expected}"
    print(f"  {expected:8} <- {text!r}  route={r}")
assert route({"intent": "full"}) == ["fan_trends", "fan_amazon", "fan_news"]
print("  fan-out list OK")

print("\n== 2. Full run (fan-out merge + verdict) ==")
with SqliteSaver.from_conn_string(DB) as cp:
    app = build_graph(cp)
    cfg = {"configurable": {"thread_id": "t1"}}
    app.invoke({"messages": [HumanMessage("Is a 1L steel insulated bottle worth launching in India under 1500?")]}, cfg)
    state = app.get_state(cfg).values
    sources = sorted(r["source"] for r in state["research"])
    print("  research sources merged:", sources)
    assert sources == ["amazon_search", "google_news", "google_trends"], sources
    print("  verdict:", state["verdict"])
    assert state["verdict"] == "Go"

print("\n== 3. Memory survives restart (new graph, same thread/db) ==")
with SqliteSaver.from_conn_string(DB) as cp:
    app2 = build_graph(cp)
    cfg = {"configurable": {"thread_id": "t1"}}
    before = len(app2.get_state(cfg).values["messages"])
    app2.invoke({"messages": [HumanMessage("what about the US market?")]}, cfg)
    after = len(app2.get_state(cfg).values["messages"])
    print(f"  messages before={before} after={after}")
    assert after > before, "history did not persist/grow"

print("\n== 4. Pricing branch uses BOTH price worlds ==")
with SqliteSaver.from_conn_string(DB) as cp:
    app3 = build_graph(cp)
    cfg = {"configurable": {"thread_id": "t2"}}
    app3.invoke({"messages": [HumanMessage("what price should I sell the bottle at?")]}, cfg)
    srcs = sorted(r["source"] for r in app3.get_state(cfg).values["research"])
    print("  pricing sources:", srcs)
    assert srcs == ["amazon_search", "google_shopping"], srcs

os.remove(DB)
print("\nALL SMOKE TESTS PASSED ✅")
