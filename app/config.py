"""Central configuration.

Everything tunable lives here and is read from environment variables, so the
agent is config-driven (no hardcoded secrets). Import this module anywhere you
need a key, the mock-mode flag, or an LLM handle.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()  # read .env into the process environment


def _flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes"}


# ---- behaviour ----
MOCK_MODE: bool = _flag("MOCK_MODE", "true")
SUMMARY_TRIGGER: int = int(os.getenv("SUMMARY_TRIGGER", "10"))
CHECKPOINT_DB: str = os.getenv("CHECKPOINT_DB", "launchlens.sqlite")
# Max tool calls the agent may make in ONE turn. The agent<->tools loop is
# otherwise unbounded -- a chatty model can fire dozens of paid API queries on a
# single question and drain a quota. Once this many tool results are gathered in
# a turn, the agent is re-invoked WITHOUT tools so it must answer from what it
# has. Tune with TOOL_BUDGET in the environment.
TOOL_BUDGET: int = int(os.getenv("TOOL_BUDGET", "6"))

# ---- LLM ----
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "qwen")
LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen-plus")
LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "60"))  # seconds; no hangs forever
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Qwen cloud (Alibaba DashScope) — OpenAI-compatible endpoint.
QWEN_API_KEY = os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
QWEN_BASE_URL = os.getenv(
    "QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
)

# ---- data providers ----
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
OXYLABS_USERNAME = os.getenv("OXYLABS_USERNAME")
OXYLABS_PASSWORD = os.getenv("OXYLABS_PASSWORD")


def get_llm(tools: list | None = None):
    """Return a chat model, optionally bound to tools.

    Imported lazily so the graph can be built/inspected without the LLM SDK
    installed or an API key present (useful for tests and CI).
    """
    if LLM_PROVIDER == "qwen":
        # Qwen cloud (DashScope) speaks the OpenAI API, so we reuse ChatOpenAI
        # with a custom base_url. Qwen models support tool/function calling.
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=LLM_MODEL,
            temperature=0,
            api_key=QWEN_API_KEY,
            base_url=QWEN_BASE_URL,
            timeout=LLM_TIMEOUT,
            max_retries=2,
        )
    elif LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model=LLM_MODEL, temperature=0, api_key=OPENAI_API_KEY,
                         timeout=LLM_TIMEOUT, max_retries=2)
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")

    return llm.bind_tools(tools) if tools else llm
