"""Oxylabs tools -- the SUPPLY side (what actually sells on Amazon).

Three sources are exposed: amazon_search (listings), amazon_product (full page
incl. reviews/complaints) and amazon_bestsellers (category leaders). Each returns
SLIM JSON, never the raw scrape, so the LLM gets only what it needs.
"""
from __future__ import annotations

from langchain_core.tools import tool

from .. import config
from ._common import clip, load_fixture

try:
    import requests
except ImportError:
    requests = None

_OXY = "https://realtime.oxylabs.io/v1/queries"


def _scrape(payload: dict) -> dict:
    """Call Oxylabs Realtime API with basic auth. Returns first result's content."""
    if requests is None:
        raise RuntimeError("`requests` not installed; cannot make live calls.")
    resp = requests.post(
        _OXY,
        auth=(config.OXYLABS_USERNAME, config.OXYLABS_PASSWORD),
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    return (results[0].get("content") if results else {}) or {}


# ---------- plain fetchers (used directly by fan-out nodes) ----------

def fetch_amazon_search(query: str, domain: str = "com") -> dict:
    """Amazon keyword search -> top listings with price/rating/reviews."""
    if config.MOCK_MODE:
        return load_fixture("amazon_search.json")
    content = _scrape({"source": "amazon_search", "query": query, "domain": domain,
                       "parse": True})
    items = [
        {"asin": r.get("asin"), "title": r.get("title"), "price": r.get("price"),
         "rating": r.get("rating"), "reviews": r.get("reviews_count")}
        for r in clip(content.get("results", {}).get("organic", []), 5)
    ]
    return {"results": items, "category": query}


def fetch_amazon_product(asin: str, domain: str = "com") -> dict:
    """Amazon product page -> price, rating and mined review complaints/praises."""
    if config.MOCK_MODE:
        return load_fixture("amazon_product.json")
    content = _scrape({"source": "amazon_product", "query": asin, "domain": domain,
                       "parse": True})
    return {
        "asin": asin,
        "title": content.get("title"),
        "price": content.get("price"),
        "rating": content.get("rating"),
        "review_count": content.get("reviews_count"),
        "top_complaints": clip([r.get("content") for r in content.get("reviews", [])
                                if (r.get("rating") or 5) <= 3], 5),
    }


def fetch_amazon_bestsellers(category: str, domain: str = "com") -> dict:
    """Amazon category bestsellers -> ranked leaders with price/rating."""
    if config.MOCK_MODE:
        return load_fixture("amazon_bestsellers.json")
    content = _scrape({"source": "amazon_bestsellers", "query": category,
                       "domain": domain, "parse": True})
    items = [
        {"rank": r.get("rank"), "asin": r.get("asin"), "title": r.get("title"),
         "price": r.get("price"), "rating": r.get("rating")}
        for r in clip(content.get("results", []), 5)
    ]
    return {"category": category, "bestsellers": items}


# ---------- LangChain tools (bound to the agent) ----------

@tool
def amazon_search(query: str) -> dict:
    """Search Amazon for products matching `query`.

    Returns top listings with price, rating and review counts -- the real supply
    side: what is actually selling and at what price.
    """
    return fetch_amazon_search(query)


@tool
def amazon_product(asin: str) -> dict:
    """Get one Amazon product's details by ASIN, including mined review complaints.

    Recurring complaints (e.g. "lid leaks") are product gaps a founder can exploit.
    """
    return fetch_amazon_product(asin)


@tool
def amazon_bestsellers(category: str) -> dict:
    """Get Amazon bestsellers for a category.

    Returns the ranked leaders with prices/ratings -- the competition to beat.
    """
    return fetch_amazon_bestsellers(category)
