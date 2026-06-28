"""Generate the LaunchLens submission deck (slides/LaunchLens.pptx).

Reproducible: `python slides/build_deck.py` rebuilds the .pptx from scratch.
Pure python-pptx, no template files -- styling is defined inline below so the
deck is fully version-controlled. Export to PDF from PowerPoint/Google Slides
for submission.
"""
from __future__ import annotations

import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Emu, Inches, Pt

# ---- palette ----
INDIGO = RGBColor(0x4F, 0x46, 0xE5)
DARK = RGBColor(0x1E, 0x1B, 0x4B)
EMERALD = RGBColor(0x10, 0xB9, 0x81)
SLATE = RGBColor(0x33, 0x3A, 0x4A)
GREY = RGBColor(0x6B, 0x72, 0x80)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT = RGBColor(0xF3, 0xF4, 0xF6)

# 16:9
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
SW, SH = prs.slide_width, prs.slide_height
BLANK = prs.slide_layouts[6]


def _txt(slide, left, top, width, height):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    return tf


def _set(run, size, color, bold=False, font="Segoe UI"):
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.name = font


def _rect(slide, left, top, width, height, color):
    from pptx.enum.shapes import MSO_SHAPE
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shp.fill.solid()
    shp.fill.fore_color.rgb = color
    shp.line.fill.background()
    shp.shadow.inherit = False
    return shp


def content_slide(title, kicker, bullets):
    """Standard content slide: kicker + title + accent rule + bullet body."""
    s = prs.slides.add_slide(BLANK)
    _rect(s, 0, 0, Inches(0.28), SH, INDIGO)            # left spine
    # kicker
    tf = _txt(s, Inches(0.8), Inches(0.5), Inches(11.8), Inches(0.4))
    r = tf.paragraphs[0].add_run(); r.text = kicker.upper()
    _set(r, 13, EMERALD, bold=True)
    # title
    tf = _txt(s, Inches(0.8), Inches(0.9), Inches(11.8), Inches(1.0))
    r = tf.paragraphs[0].add_run(); r.text = title
    _set(r, 32, DARK, bold=True)
    _rect(s, Inches(0.83), Inches(1.85), Inches(1.3), Pt(4), EMERALD)
    # bullets
    tf = _txt(s, Inches(0.83), Inches(2.15), Inches(11.7), Inches(4.9))
    for i, (lead, rest) in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(12)
        b = p.add_run(); b.text = ("• " + lead)
        _set(b, 18, INDIGO, bold=True)
        if rest:
            r = p.add_run(); r.text = "  " + rest
            _set(r, 18, SLATE)
    return s


# ----------------------------------------------------------------- 1. TITLE
s = prs.slides.add_slide(BLANK)
_rect(s, 0, 0, SW, SH, DARK)
_rect(s, 0, Inches(4.55), SW, Inches(0.08), EMERALD)
tf = _txt(s, Inches(0.9), Inches(2.3), Inches(11.5), Inches(1.6))
r = tf.paragraphs[0].add_run(); r.text = "LaunchLens"
_set(r, 60, WHITE, bold=True)
r = tf.paragraphs[0].add_run(); r.text = "  🔭"
_set(r, 50, WHITE)
tf = _txt(s, Inches(0.95), Inches(3.55), Inches(11.5), Inches(1.0))
r = tf.paragraphs[0].add_run()
r.text = "Should you launch it? A market-intelligence copilot that fuses demand + supply into one Go / No-Go / Niche verdict."
_set(r, 20, RGBColor(0xC7, 0xD2, 0xFE))
tf = _txt(s, Inches(0.95), Inches(4.8), Inches(11.5), Inches(0.6))
r = tf.paragraphs[0].add_run()
r.text = "Ruby Gunna  ·  Agent Builder 2026 — Assignment 3  ·  LangGraph + SerpApi + Oxylabs"
_set(r, 15, RGBColor(0x9C, 0xA3, 0xAF))

# ----------------------------------------------------------------- 2. PROBLEM
content_slide(
    "Founders launch on gut feel — and the signals are scattered",
    "The problem",
    [("Demand lives in one place", "Google Trends, News, Shopping — is anyone searching, is it seasonal, what does it cost elsewhere?"),
     ("Supply lives in another", "Amazon — who already sells it, at what price, and what do reviews complain about?"),
     ("Nobody fuses them", "A trend chart alone says 'maybe'. A competitor list alone says 'crowded'. The answer is in the overlap."),
     ("Result", "Weeks of manual research, or an expensive guess. Founders need a fast, evidence-backed verdict.")],
)

# ----------------------------------------------------------------- 3. WHAT IT DOES
content_slide(
    "One question in, one judgement out",
    "What LaunchLens does",
    [("Ask in plain English", "“Should I launch a $20 meal-prep container set in the US?”"),
     ("It gathers evidence", "Pulls demand (Google) + supply (Amazon) live, in parallel, then reasons across both."),
     ("It returns a verdict", "Go / No-Go / Niche — with a price band, positioning angle, and a confidence level."),
     ("It remembers", "Follow-ups (“what about Canada?”) keep context across the whole conversation.")],
)

# ----------------------------------------------------------------- 4. DEMO FLOW
content_slide(
    "A founder conversation, end to end",
    "Demo flow",
    [("1 · Idea", "“Is a 32oz insulated steel bottle worth launching in the US under $40?” → full fan-out + verdict."),
     ("2 · Price", "“What price should I sell it at?” → pricing branch: Google Shopping + Amazon together."),
     ("3 · Pain", "“What are reviewers complaining about?” → mined Amazon review complaints."),
     ("4 · Memory", "“Now compare with Canada.” → remembers the product across turns."),
     ("5 · Recall", "“What did we conclude earlier?” → summarization keeps long chats coherent.")],
)

# ----------------------------------------------------------------- 5. ARCHITECTURE
s = content_slide(
    "A typed LangGraph state machine",
    "Architecture",
    [("START → summarize", "Memory node compresses old turns once the chat grows (keeps context bounded)."),
     ("→ router", "Classifies intent: demand / pricing / full / chat — conditional edges pick the path."),
     ("→ fan-out", "On 'full', three nodes (Trends · Amazon · News) run in PARALLEL and merge."),
     ("→ agent ⇄ tools", "LLM bound to 6 tools loops until it has enough evidence."),
     ("→ verdict → END", "Parses the Go / No-Go / Niche label + confidence into state.")],
)
# mini node-flow strip along the bottom
flow = ["summarize", "router", "fan-out ×3", "agent ⇄ tools", "verdict"]
x = Inches(0.83); y = Inches(6.55); w = Inches(2.25); gap = Inches(0.15)
for i, label in enumerate(flow):
    box = _rect(s, x, y, w, Inches(0.6), LIGHT if i % 2 else INDIGO)
    tf = box.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = label
    _set(r, 12, DARK if i % 2 else WHITE, bold=True)
    x = Emu(int(x) + int(w) + int(gap))

# ----------------------------------------------------------------- 6. FIVE CONCEPTS
content_slide(
    "The five required concepts, mapped to code",
    "Under the hood",
    [("1 · Graph & state", "Typed StateGraph + reducer channels  —  state.py 16/28, graph.py 28"),
     ("2 · Fan-out (parallel)", "Router returns a 3-node list, results merge  —  graph.py 49–65, nodes.py 98/104/110"),
     ("3 · Routing", "Intent → conditional edges, chat = default  —  router.py 65/81, graph.py 49"),
     ("4 · Agent + tools", "LLM ⇄ ToolNode loop over 6 tools  —  nodes.py 135, graph.py 41/68"),
     ("5 · Short-term memory", "SqliteSaver checkpointer + summarization  —  main.py 140, nodes.py 64")],
)

# ----------------------------------------------------------------- 7. DATA FUSION (core)
sf = prs.slides.add_slide(BLANK)
_rect(sf, 0, 0, SW, SH, WHITE)
_rect(sf, 0, 0, Inches(0.28), SH, EMERALD)
tf = _txt(sf, Inches(0.8), Inches(0.5), Inches(11.8), Inches(0.4))
r = tf.paragraphs[0].add_run(); r.text = "THE CORE IDEA"
_set(r, 13, EMERALD, bold=True)
tf = _txt(sf, Inches(0.8), Inches(0.9), Inches(11.8), Inches(1.0))
r = tf.paragraphs[0].add_run(); r.text = "Data fusion: one judgement, never two reports"
_set(r, 32, DARK, bold=True)
# two columns
demand = _rect(sf, Inches(0.83), Inches(2.1), Inches(5.5), Inches(2.5), RGBColor(0xEE, 0xF2, 0xFF))
tf = demand.text_frame; tf.word_wrap = True; tf.margin_left = Inches(0.25); tf.margin_top = Inches(0.2)
p = tf.paragraphs[0]; r = p.add_run(); r.text = "DEMAND  ·  Google / SerpApi"; _set(r, 16, INDIGO, bold=True)
for t in ["Trends — interest + seasonality (relative index, read with care)",
          "News — launches, recalls, market shifts",
          "Shopping — cross-retailer price reality"]:
    p = tf.add_paragraph(); p.space_before = Pt(6); r = p.add_run(); r.text = "• " + t; _set(r, 13.5, SLATE)
supply = _rect(sf, Inches(7.0), Inches(2.1), Inches(5.5), Inches(2.5), RGBColor(0xEC, 0xFD, 0xF5))
tf = supply.text_frame; tf.word_wrap = True; tf.margin_left = Inches(0.25); tf.margin_top = Inches(0.2)
p = tf.paragraphs[0]; r = p.add_run(); r.text = "SUPPLY  ·  Amazon / Oxylabs"; _set(r, 16, EMERALD, bold=True)
for t in ["Search — who already sells it, at what price",
          "Product — mined review complaints (the gaps)",
          "Bestsellers — how entrenched the competition is"]:
    p = tf.add_paragraph(); p.space_before = Pt(6); r = p.add_run(); r.text = "• " + t; _set(r, 13.5, SLATE)
# fusion bar
fuse = _rect(sf, Inches(0.83), Inches(4.95), Inches(11.67), Inches(1.6), DARK)
tf = fuse.text_frame; tf.word_wrap = True; tf.margin_left = Inches(0.3); tf.margin_top = Inches(0.18)
p = tf.paragraphs[0]; r = p.add_run(); r.text = "FUSED IN ONE AGENT TURN"; _set(r, 14, EMERALD, bold=True)
p = tf.add_paragraph(); r = p.add_run()
r.text = ("“Interest is rising AND the $23 bestseller's reviews complain it leaks → a real, "
          "differentiable gap.”  The agent weighs demand × supply × unit-economics together and "
          "emits Go / No-Go / Niche + price band + confidence — not a demand report next to a supply report.")
_set(r, 14.5, WHITE)

# ----------------------------------------------------------------- 8. TOOLS
content_slide(
    "Six tools, two providers, slim JSON",
    "Tool inventory",
    [("google_trends", "Demand curve + related queries, slope-classified (not noise-read)."),
     ("google_news", "Recent landscape: launches, recalls, competitor moves."),
     ("google_shopping", "Cross-retailer price range for the price band."),
     ("amazon_search", "Live listings, prices, ratings, review counts."),
     ("amazon_product", "Per-ASIN detail incl. mined review complaints."),
     ("amazon_bestsellers", "Category leaders → how crowded / entrenched it is."),
     ("Every tool returns slim JSON", "A few fields, never the raw payload — keeps tokens + context bounded.")],
)

# ----------------------------------------------------------------- 9. MEMORY
content_slide(
    "Memory that survives restarts and long chats",
    "Short-term memory",
    [("Checkpointer", "SqliteSaver persists full state after every node, keyed by thread_id — quit and resume."),
     ("Summarization node", "Once the chat grows, old plain messages fold into a rolling summary."),
     ("Tool history stays intact", "Only Human/AI text is compressed; tool-call sequences are never broken."),
     ("Why it matters", "Per-turn cost stays roughly flat instead of growing with conversation length.")],
)

# ----------------------------------------------------------------- 10. VERDICT
content_slide(
    "A verdict you can trust — and challenge",
    "Verdict + confidence",
    [("Conditional, not absolute", "“Go IF COGS < $X and a defensible feature exists” — verdicts state their bar."),
     ("Confidence level", "High / Medium / Low, lowered when a data source comes back empty."),
     ("Trend sanity", "Treats Trends as a relative, seasonal index — a 5→10 move isn't 'demand doubling'."),
     ("Quantified complaints", "Weighs how common an issue is, not one cherry-picked review."),
     ("Unit-economics aware", "Prompts margin reasoning: COGS, marketplace fees, ad cost before a Go.")],
)

# ----------------------------------------------------------------- 11. TECH STACK
content_slide(
    "Tech stack",
    "How it's built",
    [("Orchestration", "LangGraph typed StateGraph + checkpointer."),
     ("LLM", "Tool-calling chat model via a swappable config factory."),
     ("Demand data", "SerpApi — Google Trends / News / Shopping."),
     ("Supply data", "Oxylabs — Amazon search / product / bestsellers."),
     ("Persistence", "SQLite locally; swap SqliteSaver → PostgresSaver for prod (same interface)."),
     ("Runs offline", "MOCK_MODE serves fixtures — full graph testable with no keys.")],
)

# ----------------------------------------------------------------- 12. NEXT
content_slide(
    "Limitations & what's next",
    "Roadmap",
    [("Keyword routing", "Cheap and explainable; an LLM classifier would handle ambiguous phrasing better."),
     ("Live-schema hardening", "Parsers should be defensive against provider schema drift."),
     ("Unit-economics module", "Turn margin reasoning into a real FBA fee + COGS calculator (in README roadmap)."),
     ("Production", "Postgres checkpointer for multi-user, a small eval harness, richer streaming UI.")],
)

out = os.path.join(os.path.dirname(__file__), "LaunchLens.pptx")
prs.save(out)
print("wrote", out, "—", len(prs.slides.__iter__.__self__._sldIdLst), "slides")
