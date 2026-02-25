# Agent Roles — Detailed Definitions

---

## Team Lead (Orchestrator)

- **Model**: Opus 4.6 (best reasoning for synthesis and decision-making)
- **Skills**: trading-orchestrator
- **MCP access**: None directly (delegates ALL data fetching to teammates)
- **Responsibilities**:
  - Coordinate trading cycles (initiate, sequence, conclude)
  - Synthesize technical + sentiment data into trade decisions
  - Apply the decision matrix and confidence framework
  - Log cycle summaries for audit trail
  - Monitor overall portfolio health
- **MUST NEVER**:
  - Place orders directly (only Executor does this)
  - Fetch market data directly (delegates to Screener)
  - Fetch news/sentiment directly (delegates to Analyst)
  - Bypass or override the Executor's risk checks
- **Communication pattern**: Receives structured reports from all teammates, sends task assignments with specific instructions

---

## Screener Agent

- **Model**: Sonnet (cost-effective for high-volume scanning)
- **Skills**: market-data, technical-analysis
- **MCP access**: angel-one-mcp
- **Responsibilities**:
  - Scan all 50 Nifty 50 stocks each cycle
  - Fetch historical candles and compute technical indicators (RSI, MACD, EMA, volume)
  - Calculate composite technical score for each stock
  - Flag stocks with composite score >= 60 for Analyst review
- **Output format**:
  ```json
  {
    "symbol": "RELIANCE-EQ",
    "composite_score": 78,
    "classification": "BUY",
    "confidence": "HIGH",
    "indicators": {
      "rsi": 32.5,
      "macd_signal": "BULLISH_CROSS",
      "ema_trend": "ABOVE_ALL",
      "volume_ratio": 1.8
    },
    "notes": "Oversold bounce with volume confirmation"
  }
  ```
- **Efficiency tips**:
  - Use `get_watchlist_quotes()` for batch pricing (single API call for all 50 stocks)
  - Use `get_nifty50_symbols()` to get the current constituent list
  - Minimize individual `get_historical_candles()` calls; only fetch for stocks showing initial promise
- **When no stocks flagged**: Report back to Lead with "no opportunities found" -- this is a valid outcome

---

## Analyst Agent

- **Model**: Sonnet
- **Skills**: sentiment-analysis, market-data
- **MCP access**: news-sentiment-mcp, angel-one-mcp
- **Responsibilities**:
  - Deep-dive ONLY on stocks flagged by Screener (not all 50)
  - Fetch recent news via `get_stock_news()`
  - Score sentiment (BULLISH / NEUTRAL / BEARISH)
  - Detect red flags (SEBI investigations, fraud allegations, management exits, etc.)
  - Provide sector context via `get_sector_performance()`
  - Check FII/DII activity via `get_fii_dii_data()`
  - Check India VIX for market-wide risk via `get_india_vix()`
- **Output format**:
  ```json
  {
    "symbol": "RELIANCE-EQ",
    "sentiment_score": 65,
    "sentiment_label": "BULLISH",
    "red_flags": [],
    "key_drivers": ["Q3 earnings beat by 12%", "Jio subscriber growth"],
    "sector_context": "Energy sector neutral, downstream performing well",
    "fii_dii_trend": "FII net buyers this week",
    "vix_level": 14.2,
    "vix_assessment": "LOW_VOLATILITY"
  }
  ```
- **Activation**: Only when Screener produces flagged stocks. If Screener reports zero flags, Analyst is NOT activated (saves API calls and cost).
- **Red flag examples**: SEBI investigation, auditor resignation, promoter pledge increase, earnings miss > 10%, credit rating downgrade

---

## Executor Agent

- **Model**: Sonnet
- **Skills**: portfolio-management
- **MCP access**: angel-one-mcp, portfolio-db-mcp
- **Responsibilities**:
  - Validate ALL risk rules before any trade
  - Calculate position sizes based on confidence level and available capital
  - Place orders via Angel One API
  - Log every trade with full reasoning
  - Update position records
  - Monitor existing positions against stop-losses
- **Output format**:
  ```json
  {
    "symbol": "RELIANCE-EQ",
    "action": "BUY",
    "quantity": 4,
    "price": 2500.00,
    "stop_loss": 2425.00,
    "order_id": "ORD123456",
    "status": "EXECUTED",
    "risk_check_result": "APPROVED"
  }
  ```
- **MUST ALWAYS**:
  1. Call `check_risk_limits()` BEFORE `place_order()` -- no exceptions
  2. If `check_risk_limits()` returns `approved: false`, DO NOT proceed. Report rejection to Lead.
  3. Log every trade via `log_trade()` with full reasoning, scores, and indicators
  4. Update position via `update_position()` after confirmed execution
- **Safety principle**: When in doubt, REJECT the trade. Missing a profitable trade is always better than taking a bad one.

---

## Agent Interaction Flow

```
Lead assigns scan task
    |
    v
Screener scans Nifty 50 --> returns flagged stocks (or none)
    |
    v
Lead assigns analysis task (only if flags exist)
    |
    v
Analyst deep-dives flagged stocks --> returns sentiment + red flags
    |
    v
Lead applies decision matrix --> decides BUY / SKIP / HOLD
    |
    v
Lead assigns execution task (only for BUY decisions)
    |
    v
Executor validates risk --> places order --> logs trade
    |
    v
Lead logs cycle summary
```
