"""SerpApi tools -- the DEMAND side (what the market wants).

Two engines are exposed as LangChain tools: Google Trends and Google News,
plus a Google Shopping fetcher used by the pricing branch. Each returns SLIM
JSON (a handful of fields), never the raw SerpApi payload -- this keeps token
cost and context size down (graded under code quality).
"""
from __future__ import annotations

from langchain_core.tools import tool

from .. import config
from ._common import clip, load_fixture

try:
    import requests
except ImportError:  # requests only needed for live mode
    requests = None

_SERPAPI = "https://serpapi.com/search"


def _classify_trend(vals: list) -> tuple:
    """Classify a Google Trends series WITHOUT over-reading it.

    Trends values are a 0-100 RELATIVE index, not unit volume, so a small
    absolute move (e.g. 5 -> 10) is noise-level even though it 'doubles'. We
    compare the back third against the front third and require a >=10-point
    slope before calling it rising/declining, treat a low peak as flat, and
    always attach a caveat that the index is seasonal + relative.
    """
    if len(vals) < 4:
        return "unknown", "Too few data points to judge a trend."
    third = max(1, len(vals) // 3)
    early = sum(vals[:third]) / third
    late = sum(vals[-third:]) / third
    delta = late - early
    if max(vals) < 25:
        direction = "low/flat"
    elif delta >= 10:
        direction = "rising"
    elif delta <= -10:
        direction = "declining"
    else:
        direction = "flat"
    note = ("Google Trends is a 0-100 RELATIVE, seasonal index -- not unit "
            "volume. Confirm against absolute demand and seasonality before "
            "weighting heavily.")
    return direction, note


def _get(params: dict) -> dict:
    """Call SerpApi with the shared key. Raises on HTTP error."""
    if requests is None:
        raise RuntimeError("`requests` not installed; cannot make live calls.")
    resp = requests.get(
        _SERPAPI, params={**params, "api_key": config.SERPAPI_API_KEY}, timeout=30
    )
    resp.raise_for_status()
    return resp.json()


# ---------- plain fetchers (used directly by fan-out nodes) ----------

def fetch_trends(query: str) -> dict:
    """Google Trends: interest over time + related queries for `query`."""
    if config.MOCK_MODE:
        data = load_fixture("trends.json")
        return {"query": query, **data}
    # Google Trends rejects queries over ~100 chars -- clip as a last-resort guard
    raw = _get({"engine": "google_trends", "q": query[:95], "data_type": "TIMESERIES"})
    timeline = raw.get("interest_over_time", {}).get("timeline_data", [])
    points = [
        {"date": p.get("date"), "value": (p.get("values") or [{}])[0].get("extracted_value")}
        for p in clip(timeline, 12)
    ]
    vals = [p["value"] for p in points if isinstance(p["value"], int)]
    trend, trend_note = _classify_trend(vals)
    related = [r.get("query") for r in raw.get("related_queries", {}).get("top", [])]
    return {"query": query, "interest_points": points, "trend": trend,
            "trend_note": trend_note, "peak_interest": max(vals) if vals else None,
            "related_queries": clip(related, 6)}


def fetch_news(query: str) -> dict:
    """Google News: recent market events, launches, recalls for `query`."""
    if config.MOCK_MODE:
        return load_fixture("news.json")
    raw = _get({"engine": "google_news", "q": query})
    arts = [
        {"title": a.get("title"), "source": (a.get("source") or {}).get("name"),
         "date": a.get("date")}
        for a in clip(raw.get("news_results", []), 5)
    ]
    return {"articles": arts}


def fetch_shopping(query: str) -> dict:
    """Google Shopping: cross-retailer prices for `query`."""
    if config.MOCK_MODE:
        return load_fixture("shopping.json")
    raw = _get({"engine": "google_shopping", "q": query})
    offers = [
        {"title": o.get("title"), "price": o.get("extracted_price"),
         "source": o.get("source"), "rating": o.get("rating")}
        for o in clip(raw.get("shopping_results", []), 6)
    ]
    prices = [o["price"] for o in offers if isinstance(o["price"], (int, float))]
    pr = {"low": min(prices), "high": max(prices)} if prices else {}
    return {"offers": offers, "price_range": pr}


# ---------- LangChain tools (bound to the agent) ----------

@tool
def google_trends(query: str) -> dict:
    """Check demand for a product idea on Google Trends.

    Returns whether search interest is rising/flat/declining over recent months
    plus the hottest related search queries. Use this to judge demand.
    """
    return fetch_trends(query)


@tool
def google_news(query: str) -> dict:
    """Scan recent news for a product/category on Google News.

    Returns recent headlines: launches, recalls, competitor moves, market growth.
    Use this to understand the current landscape and risks.
    """
    return fetch_news(query)


@tool
def google_shopping(query: str) -> dict:
    """Look up cross-retailer prices for a product on Google Shopping.

    Returns a slim list of offers with prices and the overall price range.
    Use this with Amazon pricing to decide where a target price should sit.
    """
    return fetch_shopping(query)
