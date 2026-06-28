# LaunchLens — 2-minute demo recording script

A production shot list for the submission video (≥2 min). It must explain what
LaunchLens is + the problem it solves, and show it **actually running** — a real
conversation with a Go/No-Go verdict and **memory across turns**.

## Weave strategy

- **Slides = the story** (problem → product → architecture). ~45s.
- **Terminal = the proof** (real run + memory). ~80s.
- **Pause = your edit tool.** Type a prompt → Enter → **PAUSE** while the live
  API calls churn (5–15s) → **RESUME** when the verdict lands → narrate over the
  result. No dead air.
- Keep **call #1 fully live** (show the streaming steps) to prove authenticity;
  pause-skip the waits on calls #2–4. Pausing *every* call can read as faked —
  one live call + paused waits is tight *and* credible.

## Shot list (~2:15)

| # | Screen | Say (narrate) | Do / cue |
|---|--------|---------------|----------|
| 1 | Cover slide | "Before every launch, founders ask one scary question — will anyone actually buy this? LaunchLens answers it." | Hold 4s |
| 2 | Problem slide | "Demand lives on Google. Supply lives on Amazon. Nobody fuses them — a trend says 'maybe', a competitor list says 'crowded'. The answer's in the overlap." | ~10s |
| 3 | Architecture slide | "It's one LangGraph agent: a router, parallel fan-out to Google and Amazon, an agent-plus-tools loop, and memory across turns." | ~10s |
| 4 | Fusion / GO slide | "It fuses demand, market and price into one Go or No-Go call. Let's see it live." | ~8s → cut to terminal |
| 5 | Terminal (empty) | "Real terminal, live APIs." | run `python -m app.main` |
| 6 | Terminal — **CALL #1 LIVE** | Type: `should I launch a $20 meal-prep container set in the US?` — "Watch it stream — reading, routing, pulling Amazon through Oxylabs, scanning Google News and Trends, all live." | Let it run on-camera. This is your proof. |
| 7 | Terminal — verdict | "There's the fused verdict — Go, with a confidence level, a price band, and positioning. Not two reports — one call." | Read the verdict line aloud |
| 8 | Terminal — CALL #2 | Type: `what are buyers complaining about in the top sellers?` → **PAUSE** → resume on result → "Now it mines real Amazon review complaints to find the gap." | Pause over the wait |
| 9 | Terminal — **CALL #3 (MEMORY)** | Type: `what about a premium glass version at $35 instead?` → **PAUSE** → resume → "I never repeated 'meal-prep' or 'US' — it remembers the product and market from earlier turns. That's memory, checkpointed after every step." | **Required memory beat — say it explicitly.** |
| 10 | Terminal — CALL #4 | Type: `what did we conclude overall?` → **PAUSE** → resume → "And it summarizes the whole thread back into one recommendation." | Pause over the wait |
| 11 | Close slide | "Scattered demand and supply, fused into one evidence-backed launch verdict. Code, slides and docs are in the repo." | Hold 5s |

## The prompts (copy-paste)

```
should I launch a $20 meal-prep container set in the US?
what are buyers complaining about in the top sellers?
what about a premium glass version at $35 instead?
what did we conclude overall?
```

| Prompt | Rubric beat it proves |
|--------|-----------------------|
| `$20 meal-prep… US?` | full fan-out → live Trends + News + Shopping + Amazon → Go/No-Go verdict |
| `complaining about… top sellers?` | Oxylabs `amazon_product` review mining |
| `premium glass at $35 instead?` | **memory across turns** (no product/market restated) |
| `what did we conclude?` | summarization / recall |

## Pre-flight

- `.env`: `MOCK_MODE=false`, all keys set. Do one full **dry run** first so the
  first live call's timing is predictable.
- Start from a **fresh thread** (clean memory) so call #3 genuinely proves recall.
- Bump up the terminal font so it's readable on playback.
- If a live call errors mid-take: it degrades gracefully — say "resilient to a
  flaky API" and move on, or pause + retry.

## Timing math

Slides ~40s + terminal ~85s + close ~10s = **~2:15** — clears the 2-min floor.
Pauses cost nothing on the clock since they're cut.

## After recording

Upload unlisted to Loom/YouTube (or commit the file), then put the link in
`README.md` and `SUBMISSION.md`.
