"""Shared helpers for tools: fixture loading + safe truncation."""
from __future__ import annotations

import json
import os

_FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def load_fixture(name: str) -> dict:
    """Load a saved JSON fixture used in MOCK_MODE."""
    with open(os.path.join(_FIXTURES, name), "r", encoding="utf-8") as f:
        return json.load(f)


def clip(items: list, n: int) -> list:
    """Keep tool outputs slim: never return more than n items."""
    return items[:n]
