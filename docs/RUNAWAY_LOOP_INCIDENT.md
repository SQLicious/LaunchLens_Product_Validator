# Runaway tool-loop incident — why `TOOL_BUDGET` exists

This is the production-grade lesson that drove the deterministic per-turn tool
budget (`config.TOOL_BUDGET`, enforced in `graph.py:route_agent`). Stats below
were reconstructed from the SQLite checkpointer (`founder-session` thread).

## What happened

A single, casual follow-up message in a multi-turn demo:

> **"what about a premium glass version at $35 instead?"**

triggered **34 tool calls in one turn** — ~34 billable SerpApi/Oxylabs/LLM
round-trips for one question. It quietly drained the Qwen / data-API quota
before anyone noticed.

## The anatomy of the loop

The agent treated each **synonym reword of the same idea** as a fresh search and
re-ran its **entire 6-tool research suite** for each variant:

| Query variant re-run | Tools fired per variant |
|---|---|
| `glass meal prep containers` | trends, news, amazon_search, shopping, bestsellers |
| `premium glass meal prep containers` | trends, news, amazon_search, shopping, bestsellers |
| `borosilicate glass meal prep containers` | trends, news, amazon_search, shopping, bestsellers |
| `leakproof glass meal prep containers` | trends, news, amazon_search, shopping, bestsellers |

Plus **14 individual `amazon_product` ASIN lookups** — every product it saw,
including duplicates (`B0D4M1SMPR`, `B08X4615SC` each queried twice).

**Call breakdown (34 total):**

| Tool | Calls |
|---|---|
| `amazon_product` | 14 |
| `google_trends` | 4 |
| `google_news` | 4 |
| `amazon_search` | 4 |
| `google_shopping` | 4 |
| `amazon_bestsellers` | 4 |

## The non-obvious part

Every tool result was **tiny** — 95 to 1,334 chars of slim JSON. The context /
token discipline (tools return a few fields, never raw payloads) worked fine.
**The cost was hiding in the call count, not the token count.** Anything that
only watches context size would have seen a healthy turn while the bill ran up.

## Trigger pattern

Not an adversarial or long input. The chattiest shape is a **comparative /
refinement prompt** (*"what about X instead?"*) on a **topic already researched**
that contains a **synonym-expandable noun** (glass → borosilicate → leakproof).
Worth generating these deliberately (synthetic users) rather than waiting to hit
one by luck.

## The fix

A deterministic per-turn tool budget, enforced **in code**, not by asking the
model nicely:

- `nodes.tools_used_this_turn(state)` counts tool results since the last
  `HumanMessage` (turn boundary — resets every turn, no separate counter).
- `graph.route_agent` continues the agent↔tools loop only while
  `wants_tools AND used < TOOL_BUDGET`; otherwise routes to `verdict`.
- `agent_node` drops the tool bindings once the budget is spent, so the agent
  can't emit a trailing `tool_call` that the gate would strand without a result
  (which would also corrupt history for the next turn).

Default `TOOL_BUDGET=6`. On the incident turn that is an **~82% reduction**
(34 → 6 calls). Reliability comes from the graph, not the prompt.

## Takeaway

Autonomous agents don't fail loudly — they fail expensively. Cost (call count,
not just tokens) is a first-class engineering constraint and must be bounded
deterministically in the control flow.
