"""
Fetch news headlines for a stock from free RSS sources.
Stub — actual execution goes through the news-sentiment-mcp MCP server.

In production, use get_stock_news() and get_market_news() MCP tools.
"""

from urllib.parse import quote_plus


def get_google_news_url(query: str) -> str:
    """Build Google News RSS URL for a stock query."""
    encoded = quote_plus(f"{query} stock NSE")
    return f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN"


def get_et_markets_url() -> str:
    """Economic Times Markets RSS feed URL."""
    return "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"


def fetch_stock_news(symbol: str, company_name: str = "", max_results: int = 10) -> list[dict]:
    """
    Fetch recent news for a stock.

    Args:
        symbol: Stock symbol (e.g., "RELIANCE" without -EQ suffix)
        company_name: Full company name for better search results
        max_results: Max news items to return

    Returns:
        List of {title, link, description, published, source}
    """
    # In production, use news-sentiment-mcp get_stock_news() tool
    raise NotImplementedError(
        "Use the news-sentiment-mcp get_stock_news() tool instead."
    )


if __name__ == "__main__":
    print("This is a stub. Use the news-sentiment-mcp MCP tools.")
    print(f"Google News URL example: {get_google_news_url('Reliance Industries')}")
    print(f"ET Markets RSS: {get_et_markets_url()}")
