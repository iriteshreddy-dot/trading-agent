---
name: market-data
description: Fetch and interpret Indian stock market data via Angel One SmartAPI. Use this skill whenever you need live prices, historical candles, watchlist data, or any market data for NSE/BSE stocks. Trigger this for any mention of stock prices, market data, Nifty 50, Angel One, or when preparing data for technical analysis. Also use when checking if the market is open, refreshing API sessions, or handling symbol lookups.
---

# Market Data Skill — Angel One SmartAPI

## Overview

This skill provides instructions for fetching and working with Indian stock market data through Angel One's SmartAPI. All market data operations go through the `angel-one-mcp` MCP server.

## Authentication

Angel One SmartAPI uses a session-based auth flow:
1. Login with client ID + PIN + TOTP
2. Receive JWT token + refresh token
3. Token expires after market hours — refresh before each trading session

**Before any data fetch, always check session validity. If expired, call `refresh_session()` first.**

## Symbol Convention

Angel One uses its own token system alongside exchange symbols:
- Format: `{exchange}:{tradingsymbol}` → e.g., `NSE:RELIANCE-EQ`
- The MCP server handles symbol resolution internally
- Refer to `references/nifty50-symbols.md` for the complete Nifty 50 mapping

## Available Data Operations

### Live Quotes
```
Tool: get_live_quote(symbol)
Returns: LTP, open, high, low, close, volume, bid/ask
Use for: Current price checks, real-time monitoring
```

### Historical Candles
```
Tool: get_historical_candles(symbol, interval, from_date, to_date)
Intervals: ONE_MINUTE, FIVE_MINUTE, FIFTEEN_MINUTE, ONE_HOUR, ONE_DAY
Returns: Array of [timestamp, open, high, low, close, volume]
Use for: Technical analysis, backtesting, pattern detection
```

### Batch Watchlist
```
Tool: get_watchlist_quotes()
Returns: LTP + change% for all Nifty 50 stocks
Use for: Screening cycles, market breadth analysis
```

## Market Hours (IST)

- Pre-market: 9:00 AM - 9:15 AM
- Regular session: 9:15 AM - 3:30 PM
- Post-market: 3:40 PM - 4:00 PM
- **Active trading window: 9:30 AM - 3:15 PM** (avoid first/last 15 min)

Before fetching live data, run `scripts/check_market_status.py` to verify market is open. On holidays and weekends, only historical data is available.

## Rate Limits

- Max 10 requests per second
- Max 3000 requests per day on free tier
- Batch endpoints (watchlist) count as 1 request regardless of stock count
- **Always prefer batch endpoints over individual calls during screening**

## Error Handling

| Error | Meaning | Action |
|-------|---------|--------|
| Session expired | JWT token invalid | Call refresh_session(), retry |
| Symbol not found | Invalid token/symbol | Check nifty50-symbols.md reference |
| Market closed | No live data available | Use historical data only |
| Rate limited | Too many requests | Wait 1 second, retry with backoff |
| Network timeout | API unreachable | Log error, skip this cycle |

## Data Freshness

- Live quotes: Real-time during market hours
- Historical candles: ~1 minute delay
- After market close: Last traded price is final
- **Never make trading decisions on stale data (>5 min old during market hours)**

## Reference Files

- `references/nifty50-symbols.md` — Complete symbol mapping for Nifty 50 stocks
- `references/market-hours.md` — Trading calendar, holidays, special sessions
