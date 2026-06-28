"""LaunchLens CLI chat loop.

Run:  python -m app.main            (resumes the default thread)
      python -m app.main --thread X (use a named conversation thread)

Memory: state is checkpointed to SQLite after every node, so quitting and
re-running with the same --thread resumes the conversation.
"""
from __future__ import annotations

import argparse
import sys
import uuid

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver

from . import config
from .graph import build_graph

BANNER = r"""
  _                            _     _
 | |    __ _ _   _ _ __   ___| |__ | |    ___ _ __  ___
 | |   / _` | | | | '_ \ / __| '_ \| |   / _ \ '_ \/ __|
 | |__| (_| | |_| | | | | (__| | | | |__|  __/ | | \__ \
 |_____\__,_|\__,_|_| |_|\___|_| |_|_____\___|_| |_|___/
  Is this product worth launching?
"""

HELP = """\
How to use LaunchLens
---------------------
Just describe your product idea in plain English at the founder> prompt.
LaunchLens fuses demand signals (Google Trends/News/Shopping) with supply
signals (Amazon) into one Go / No-Go / Niche verdict.

Tip: include the product, the market, and a price for the sharpest read.

Try one of these as your first message:
  - should I launch a $20 meal-prep container set in the US?
  - is there demand for reusable beeswax food wraps?
  - what price should a stainless steel insulated water bottle sell at?
  - is the market for resistance-band home gym kits growing?

Commands (type at the founder> prompt):
  help    show this help again
  mode    show LIVE/MOCK + current thread
  exit    quit  (also: quit, or Ctrl-C)
"""


# Friendly label shown the moment each node STARTS, so the founder always sees
# where the flow is instead of staring at a frozen prompt.
_STEP_LABELS = {
    "summarize": "reading the conversation so far",
    "router": "working out what you're asking",
    "demand": "checking demand (Google Trends)",
    "pricing": "comparing prices (Google Shopping + Amazon)",
    "fan_trends": "pulling Google Trends",
    "fan_amazon": "pulling Amazon supply (Oxylabs)",
    "fan_news": "scanning Google News",
    "agent": "reasoning over the evidence",
    "tools": "running tools",
    "verdict": "scoring the verdict",
}


def _fmt_tool_call(call: dict) -> str:
    """Render an agent tool call as `name(arg=value)` with values kept short."""
    parts = []
    for k, v in (call.get("args") or {}).items():
        v = repr(v)
        parts.append(f"{k}={v[:57] + '...' if len(v) > 60 else v}")
    return f"{call.get('name')}({', '.join(parts)})"


def _agent_tool_calls(update):
    """Tool calls the agent decided on this round, as formatted strings."""
    if not isinstance(update, dict):
        return []
    return [_fmt_tool_call(call)
            for msg in update.get("messages", [])
            for call in (getattr(msg, "tool_calls", None) or [])]


def _stream_turn(app, user: str, cfg: dict) -> bool:
    """Run one turn, narrating each step and streaming the answer live.

    Three interleaved streams:
      - "debug"    -> fires when a node STARTS, so even the parallel fan-out
                      shows instant "doing X..." feedback.
      - "updates"  -> fires when a node ENDS; the agent's update carries the
                      exact tool calls it decided to make.
      - "messages" -> token deltas from the agent's reply (live streaming).
    Returns True if any answer text was streamed.
    """
    streamed = False
    mid_line = False  # True while a streamed token line is still open

    def line(text: str) -> None:
        """Print a status/tool line, breaking off any open streamed line first."""
        nonlocal mid_line
        if mid_line:
            print()
            mid_line = False
        print(text, flush=True)

    for mode, chunk in app.stream(
        {"messages": [HumanMessage(user)]}, cfg,
        stream_mode=["debug", "updates", "messages"],
    ):
        if mode == "debug":
            if chunk.get("type") == "task":
                node = chunk.get("payload", {}).get("name")
                # "tools" gets no generic label -- the exact `-> tool(...)` lines
                # already say what is running.
                label = _STEP_LABELS.get(node) if node != "tools" else None
                if label:
                    line(f"  . {label}...")
        elif mode == "updates":
            if isinstance(chunk, dict) and "agent" in chunk:
                for call in _agent_tool_calls(chunk["agent"]):
                    line(f"  -> {call}")
        elif mode == "messages":
            msg, meta = chunk
            # only stream the agent's reply tokens (skip summary/keyword LLM calls)
            if meta.get("langgraph_node") == "agent" and getattr(msg, "content", ""):
                if not streamed:
                    print("\nLaunchLens> ", end="", flush=True)
                    streamed = True
                print(msg.content, end="", flush=True)
                mid_line = True
    if mid_line:
        print()
    return streamed


def run(thread_id: str) -> None:
    cfg = {"configurable": {"thread_id": thread_id}}
    with SqliteSaver.from_conn_string(config.CHECKPOINT_DB) as checkpointer:
        app = build_graph(checkpointer)
        mode_line = f"[mode: {'MOCK' if config.MOCK_MODE else 'LIVE'} | thread: {thread_id}]"
        print(BANNER)
        print(mode_line)
        print(HELP)
        while True:
            try:
                user = input("founder> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nbye!")
                return
            cmd = user.lower()
            if cmd in {"exit", "quit"}:
                print("bye!")
                return
            if not user:
                continue
            if cmd == "help":
                print(HELP)
                continue
            if cmd == "mode":
                print(mode_line + "\n")
                continue
            try:
                streamed = _stream_turn(app, user, cfg)
                state = app.get_state(cfg).values
                if not streamed:  # fallback: nothing token-streamed (e.g. no SSE)
                    print(f"\nLaunchLens> {state['messages'][-1].content}")
                verdict = state.get("verdict")
                if verdict and verdict != "Undecided":
                    conf = state.get("confidence")
                    suffix = f", confidence: {conf}" if conf and conf != "Unknown" else ""
                    print(f"[verdict: {verdict}{suffix}]")
                print()
            except Exception as exc:  # degrade gracefully, never crash the loop
                print(f"\n[!] Something went wrong: {exc}\n")


def main() -> None:
    # Windows consoles default to cp1252; LLM replies routinely contain unicode
    # (arrows, em dashes, smart quotes). Force UTF-8 so a single stray glyph
    # never crashes a turn mid-stream.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(description="LaunchLens CLI")
    parser.add_argument("--thread", default="founder-session",
                        help="conversation thread id (resume by reusing it)")
    parser.add_argument("--new", action="store_true",
                        help="start a fresh random thread")
    args = parser.parse_args()
    thread = uuid.uuid4().hex[:8] if args.new else args.thread
    run(thread)


if __name__ == "__main__":
    main()
