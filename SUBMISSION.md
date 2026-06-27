# Submission - Assignment 3

**Student(s):** _your name(s)_
**GitHub repo:** _https://github.com/…_
**Demo video (≥2 min):** _Loom/YouTube URL or path to committed file_
**Presentation / slides:** _link to PDF/PPT/Google Slides_

---

## 1. LaunchLens in your words (2-3 sentences)

LaunchLens is a CLI chat agent that tells a founder whether a product is worth
launching. It fuses **demand** signals from Google via SerpApi (Trends, News,
Shopping) with **supply** signals from Amazon via Oxylabs (search, product
reviews, bestsellers), and the LLM agent reasons across both — e.g. "interest is
rising AND reviews complain it leaks → real opportunity" — to return a
**Go / No-Go / Niche** verdict with a price band and positioning, while
remembering the conversation across turns.

---

## 2. Concept map - where each required concept lives

| Concept | File | Function / node | Line(s) | One-line note |
|---------|------|-----------------|---------|---------------|
| Graph & state | `app/state.py`, `app/graph.py` | `State` / `merge_research`; `build_graph` | state.py 16 & 28; graph.py 30 | Typed `StateGraph`; reducer channels for messages + fan-out research. |
| Fan-out (parallel) | `app/graph.py`, `app/nodes.py` | `route` → `fan_trends`/`fan_amazon`/`fan_news` | graph.py 56–66; nodes.py 76/82/88 | Router returns a 3-node list → parallel pulls → merge on `agent`. |
| Routing (conditional edges) | `app/router.py`, `app/graph.py` | `classify_intent`, `route`; `add_conditional_edges` | router.py 31 & 45; graph.py 49 | Intent → demand / pricing / full / chat (chat = default). |
| Agent node + tools | `app/nodes.py`, `app/graph.py` | `agent_node`; `ToolNode`+`tools_condition` | nodes.py 113; graph.py 41 & 68 | LLM bound to 6 tools; agent↔tools loop; slim JSON outputs. |
| Short-term memory (checkpointer + summarization) | `app/main.py`, `app/nodes.py` | `SqliteSaver`; `summarize_node` | main.py run(); nodes.py 42 | Survives restart (thread_id) + summarization bounds context. |

---

## 3. Data sources used

- **SerpApi engine(s):** Google Trends, Google News, Google Shopping — demand, landscape, cross-retailer prices.
- **Oxylabs source(s):** amazon_search, amazon_product (reviews), amazon_bestsellers — supply, complaints, competition.
- **How they combine:** the agent reasons over demand (Trends/News) + supply (Amazon prices/reviews) in one judgement to issue the Go/No-Go/Niche verdict.
- **Live vs mocked:** MOCK_MODE=true uses `app/fixtures/`. The demo shows ≥1 live call per provider with MOCK_MODE=false.

---

## 4. How to run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill keys, or keep MOCK_MODE=true to run offline
python -m app.main
```

---

## 5. Demo script (the prompts in your recording)

1. Is a 32oz stainless-steel insulated water bottle worth launching in the US under $40?
2. What price should I sell it at?
3. What are people complaining about in the reviews?
4. Now compare it with the Canada market. (shows memory across turns)
5. (after a long chat) What did we conclude earlier? (shows summarization)

---

## 6. Bonus attempted (if any)

_e.g. long-term memory / eval harness / FastAPI UI / streaming — fill in if you add any._

---

## 7. Known limitations / what I'd do next

- Routing is keyword-based (cheap & explainable); an LLM classifier would handle ambiguous phrasing better.
- Fixtures are static in MOCK_MODE; live mode parsing should be hardened against provider schema changes.
- Next: Postgres checkpointer for multi-user prod, a small eval harness, and streaming tool-calls to the CLI.
