"""
News & Sentiment MCP Server
============================
Fetches financial news and market data from FREE sources.
No paid API keys required - uses RSS feeds, NSE data, and public endpoints.
Transport: stdio (launched by Claude Code)

Tools:
  - get_stock_news: News for a specific stock from multiple sources
  - get_market_news: General Indian market news
  - get_fii_dii_data: FII/DII daily activity from NSE
  - get_corporate_actions: Dividends, splits, bonuses from NSE
  - get_india_vix: Current India VIX (fear gauge)
  - get_sector_performance: Nifty sector indices performance
"""

import json
import logging
import re
import sys
from datetime import datetime, timedelta
from urllib.parse import quote_plus

from mcp.server.fastmcp import FastMCP

import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared import IST, now_ist

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [news-sentiment-mcp] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("news-sentiment-mcp")

mcp = FastMCP("news-sentiment-mcp", json_response=True)

# ── HTTP helpers ──────────────────────────────────────────

def _fetch_url(url: str, timeout: int = 10) -> str | None:
    """Fetch URL content, return text or None on error."""
    try:
        import urllib.request
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; TradingAgent/1.0)",
                "Accept": "application/json, text/xml, text/html, */*",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        log.warning(f"Fetch failed for {url}: {e}")
        return None


def _fetch_json(url: str, timeout: int = 10) -> dict | list | None:
    """Fetch URL and parse as JSON."""
    text = _fetch_url(url, timeout)
    if text:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            log.warning(f"JSON parse failed for {url}")
    return None


def _parse_rss(xml_text: str, max_items: int = 10) -> list[dict]:
    """Simple RSS parser - extracts title, link, description, pubDate."""
    items = []
    # Rough XML parse without external deps
    item_pattern = re.compile(r"<item>(.*?)</item>", re.DOTALL)
    for match in item_pattern.finditer(xml_text):
        block = match.group(1)

        def extract(tag):
            m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", block, re.DOTALL)
            if m:
                text = m.group(1).strip()
                # Remove CDATA
                text = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", text, flags=re.DOTALL)
                # Remove HTML tags
                text = re.sub(r"<[^>]+>", "", text)
                return text.strip()
            return ""

        items.append({
            "title": extract("title"),
            "link": extract("link"),
            "description": extract("description")[:300],
            "published": extract("pubDate"),
        })
        if len(items) >= max_items:
            break
    return items


# ══════════════════════════════════════════════════════════
# TOOLS
# ══════════════════════════════════════════════════════════


@mcp.tool()
def get_stock_news(symbol: str, company_name: str = "", max_results: int = 10) -> dict:
    """
    Get recent news for a specific stock from multiple free sources.
    Uses Google News RSS and MoneyControl RSS.

    Args:
        symbol: Stock symbol e.g. "RELIANCE" (without -EQ suffix)
        company_name: Full company name for better search e.g. "Reliance Industries"
        max_results: Maximum news items to return (default: 10)

    Returns news items with title, source, link, and published date.
    The AGENT should analyze these for sentiment - this tool just fetches.
    """
    clean_symbol = symbol.replace("-EQ", "").replace("-", " ")
    search_term = company_name if company_name else clean_symbol

    all_news = []

    # Source 1: Google News RSS (most comprehensive)
    google_url = f"https://news.google.com/rss/search?q={quote_plus(search_term + ' stock NSE')}&hl=en-IN&gl=IN&ceid=IN:en"
    google_xml = _fetch_url(google_url)
    if google_xml:
        items = _parse_rss(google_xml, max_results)
        for item in items:
            item["source"] = "Google News"
        all_news.extend(items)

    # Source 2: Economic Times RSS (if available for stock)
    et_url = f"https://economictimes.indiatimes.com/rssfeedstopstories.cms"
    et_xml = _fetch_url(et_url)
    if et_xml:
        items = _parse_rss(et_xml, 5)
        # Filter for relevant items
        for item in items:
            if clean_symbol.lower() in item["title"].lower() or clean_symbol.lower() in item["description"].lower():
                item["source"] = "Economic Times"
                all_news.append(item)

    # Deduplicate by title similarity
    seen_titles = set()
    unique_news = []
    for item in all_news:
        title_key = item["title"][:50].lower()
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_news.append(item)

    return {
        "status": "success",
        "symbol": symbol,
        "search_term": search_term,
        "count": len(unique_news[:max_results]),
        "news": unique_news[:max_results],
        "note": "Agent should analyze these headlines for sentiment scoring. Check for red flags: SEBI investigation, auditor resignation, promoter pledge, earnings miss, management changes.",
        "timestamp": now_ist().isoformat(),
    }


@mcp.tool()
def get_market_news(max_results: int = 15) -> dict:
    """
    Get general Indian stock market news from multiple RSS feeds.
    Covers: RBI policy, SEBI regulations, market-moving events.

    Args:
        max_results: Maximum news items to return
    """
    all_news = []

    # Economic Times Markets
    feeds = [
        ("https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms", "ET Markets"),
        ("https://www.livemint.com/rss/markets", "Livemint Markets"),
        ("https://news.google.com/rss/search?q=Indian+stock+market+NSE+BSE&hl=en-IN&gl=IN&ceid=IN:en", "Google News"),
    ]

    for url, source in feeds:
        xml = _fetch_url(url)
        if xml:
            items = _parse_rss(xml, max_results // len(feeds) + 1)
            for item in items:
                item["source"] = source
            all_news.extend(items)

    # Sort by recency (rough - based on pubDate strings)
    return {
        "status": "success",
        "count": len(all_news[:max_results]),
        "news": all_news[:max_results],
        "note": "Look for: RBI rate decisions, SEBI circulars, global cues (US Fed, oil prices), FII/DII flows, index-moving events.",
        "timestamp": now_ist().isoformat(),
    }


@mcp.tool()
def get_fii_dii_data() -> dict:
    """
    Get FII (Foreign Institutional Investors) and DII (Domestic Institutional Investors)
    daily buy/sell activity. Key market sentiment indicator.

    Fetched from NSE India's public API.

    Interpretation guide:
    - FII net selling > ₹2000 Cr = bearish pressure
    - FII net buying > ₹2000 Cr = bullish signal
    - DII usually provides counter-flow to FII
    """
    # NSE public endpoint for FII/DII data
    url = "https://www.nseindia.com/api/fiidiiActivity"

    # NSE requires specific headers
    try:
        import urllib.request
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Referer": "https://www.nseindia.com/",
            },
        )
        # NSE needs a session cookie - first hit the main page
        main_req = urllib.request.Request(
            "https://www.nseindia.com/",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
        )
        import http.cookiejar
        cj = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        opener.open(main_req, timeout=10)
        # Now fetch with cookies
        resp = opener.open(req, timeout=10)
        data = json.loads(resp.read().decode("utf-8"))

        if data:
            return {
                "status": "success",
                "data": data,
                "interpretation": {
                    "heavy_fii_selling": "FII net sell > ₹2000 Cr → bearish pressure, caution on long positions",
                    "heavy_fii_buying": "FII net buy > ₹2000 Cr → bullish, institutional confidence",
                    "dii_support": "Strong DII buying during FII selling → domestic support, may limit downside",
                },
                "timestamp": now_ist().isoformat(),
            }
    except Exception as e:
        log.warning(f"NSE FII/DII fetch failed: {e}")

    return {
        "status": "partial",
        "message": "Direct NSE API fetch failed. Agent should use web search for today's FII/DII data.",
        "fallback_query": "FII DII data today NSE India",
    }


@mcp.tool()
def get_corporate_actions(symbol: str = "") -> dict:
    """
    Get upcoming corporate actions (dividends, splits, bonuses, rights issues).
    Important for avoiding positions around ex-dates.

    Args:
        symbol: Stock symbol (empty for all upcoming actions)
    """
    # NSE corporate actions endpoint
    url = "https://www.nseindia.com/api/corporates-corporateActions?index=equities"
    if symbol:
        clean = symbol.replace("-EQ", "")
        url += f"&symbol={clean}"

    try:
        import urllib.request, http.cookiejar
        cj = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        main_req = urllib.request.Request(
            "https://www.nseindia.com/",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        )
        opener.open(main_req, timeout=10)

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Referer": "https://www.nseindia.com/",
            },
        )
        resp = opener.open(req, timeout=10)
        data = json.loads(resp.read().decode("utf-8"))

        actions = []
        if isinstance(data, list):
            for item in data[:20]:
                actions.append({
                    "symbol": item.get("symbol", ""),
                    "subject": item.get("subject", ""),
                    "ex_date": item.get("exDate", ""),
                    "record_date": item.get("recDate", ""),
                    "series": item.get("series", ""),
                })

        return {
            "status": "success",
            "count": len(actions),
            "actions": actions,
            "note": "AVOID new positions in stocks with ex-date within 2 trading days. Dividends cause price adjustments.",
        }
    except Exception as e:
        return {
            "status": "partial",
            "message": f"NSE corporate actions fetch failed: {e}",
            "fallback_query": f"NSE corporate actions {symbol} upcoming",
        }


@mcp.tool()
def get_india_vix() -> dict:
    """
    Get current India VIX (Volatility Index) - the market's fear gauge.

    Interpretation:
    - VIX < 12: Low fear, complacency (potential reversal risk)
    - VIX 12-15: Normal, healthy market
    - VIX 15-20: Elevated concern, be cautious with position sizes
    - VIX > 20: High fear, reduce exposure, wider stop-losses
    - VIX > 25: Extreme fear, consider not trading
    """
    try:
        import urllib.request, http.cookiejar
        cj = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        main_req = urllib.request.Request(
            "https://www.nseindia.com/",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        )
        opener.open(main_req, timeout=10)

        req = urllib.request.Request(
            "https://www.nseindia.com/api/allIndices",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Referer": "https://www.nseindia.com/",
            },
        )
        resp = opener.open(req, timeout=10)
        data = json.loads(resp.read().decode("utf-8"))

        # Find India VIX in the indices list
        for idx in data.get("data", []):
            if "VIX" in idx.get("index", "").upper():
                vix_value = idx.get("last", 0)
                vix_change = idx.get("percentChange", 0)

                # Determine risk level
                if vix_value < 12:
                    risk_level = "LOW_COMPLACENCY"
                    action = "Normal trading, but watch for complacency reversal"
                elif vix_value < 15:
                    risk_level = "NORMAL"
                    action = "Normal trading conditions"
                elif vix_value < 20:
                    risk_level = "ELEVATED"
                    action = "Reduce position sizes, tighter stop-losses"
                elif vix_value < 25:
                    risk_level = "HIGH"
                    action = "Minimal new positions, consider closing weak ones"
                else:
                    risk_level = "EXTREME"
                    action = "AVOID trading. Wait for VIX to cool below 20"

                return {
                    "status": "success",
                    "vix": vix_value,
                    "change_pct": vix_change,
                    "risk_level": risk_level,
                    "recommended_action": action,
                    "timestamp": now_ist().isoformat(),
                }

        return {"status": "error", "message": "VIX not found in indices data"}
    except Exception as e:
        return {
            "status": "partial",
            "message": f"VIX fetch failed: {e}",
            "fallback_query": "India VIX today NSE",
        }


@mcp.tool()
def get_sector_performance() -> dict:
    """
    Get performance of Nifty sector indices (Bank, IT, Pharma, Auto, etc.).
    Helps identify sector rotation and which sectors are leading/lagging.
    """
    try:
        import urllib.request, http.cookiejar
        cj = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        main_req = urllib.request.Request(
            "https://www.nseindia.com/",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        )
        opener.open(main_req, timeout=10)

        req = urllib.request.Request(
            "https://www.nseindia.com/api/allIndices",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Referer": "https://www.nseindia.com/",
            },
        )
        resp = opener.open(req, timeout=10)
        data = json.loads(resp.read().decode("utf-8"))

        # Filter for Nifty sector indices
        sector_keywords = [
            "NIFTY BANK", "NIFTY IT", "NIFTY PHARMA", "NIFTY AUTO",
            "NIFTY FMCG", "NIFTY METAL", "NIFTY REALTY", "NIFTY ENERGY",
            "NIFTY INFRA", "NIFTY PSE", "NIFTY MEDIA", "NIFTY 50",
            "NIFTY FINANCIAL", "NIFTY PRIVATE BANK", "NIFTY PSU BANK",
        ]

        sectors = []
        for idx in data.get("data", []):
            name = idx.get("index", "")
            if any(kw in name.upper() for kw in sector_keywords):
                sectors.append({
                    "index": name,
                    "last": idx.get("last"),
                    "change": idx.get("percentChange"),
                    "open": idx.get("open"),
                    "high": idx.get("high"),
                    "low": idx.get("low"),
                })

        # Sort by performance
        sectors.sort(key=lambda x: x.get("change", 0) or 0, reverse=True)

        return {
            "status": "success",
            "count": len(sectors),
            "sectors": sectors,
            "leading": sectors[:3] if sectors else [],
            "lagging": sectors[-3:] if len(sectors) >= 3 else [],
            "note": "Favor stocks in leading sectors. Avoid stocks in lagging sectors unless strong technicals override.",
            "timestamp": now_ist().isoformat(),
        }
    except Exception as e:
        return {
            "status": "partial",
            "message": f"Sector data fetch failed: {e}",
            "fallback_query": "Nifty sectoral indices performance today",
        }


# ── Entry point ───────────────────────────────────────────
if __name__ == "__main__":
    log.info("Starting News & Sentiment MCP server (stdio)")
    mcp.run(transport="stdio")
