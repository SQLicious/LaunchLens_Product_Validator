"""LaunchLens CLI chat loop.

Run:  python -m app.main            (resumes the default thread)
      python -m app.main --thread X (use a named conversation thread)

Memory: state is checkpointed to SQLite after every node, so quitting and
re-running with the same --thread resumes the conversation.
"""
from __future__ import annotations

import argparse
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
  Is this product worth launching?  (type 'exit' to quit)
"""


def run(thread_id: str) -> None:
    cfg = {"configurable": {"thread_id": thread_id}}
    with SqliteSaver.from_conn_string(config.CHECKPOINT_DB) as checkpointer:
        app = build_graph(checkpointer)
        print(BANNER)
        print(f"[mode: {'MOCK' if config.MOCK_MODE else 'LIVE'} | thread: {thread_id}]\n")
        while True:
            try:
                user = input("founder> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nbye!")
                return
            if user.lower() in {"exit", "quit"}:
                print("bye!")
                return
            if not user:
                continue
            try:
                app.invoke({"messages": [HumanMessage(user)]}, cfg)
                state = app.get_state(cfg).values
                reply = state["messages"][-1].content
                verdict = state.get("verdict")
                print(f"\nLaunchLens> {reply}")
                if verdict and verdict != "Undecided":
                    print(f"[verdict: {verdict}]")
                print()
            except Exception as exc:  # degrade gracefully, never crash the loop
                print(f"\n[!] Something went wrong: {exc}\n")


def main() -> None:
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
