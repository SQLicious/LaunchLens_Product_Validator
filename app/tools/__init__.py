"""Tool registry. ALL_TOOLS is bound to the agent and the ToolNode."""
from .serpapi_tools import google_news, google_shopping, google_trends
from .oxylabs_tools import amazon_bestsellers, amazon_product, amazon_search

ALL_TOOLS = [
    # demand (SerpApi)
    google_trends,
    google_news,
    google_shopping,
    # supply (Oxylabs)
    amazon_search,
    amazon_product,
    amazon_bestsellers,
]
