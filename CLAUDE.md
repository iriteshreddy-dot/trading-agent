# Trading Agent System v1

## What This Is
A multi-agent paper trading system for Indian stocks (Nifty 50). Capital: ₹1,00,000 simulated. NO real money.

## Architecture

```
Team Lead (Orchestrator) — coordinates, synthesizes, decides
├── Screener Agent — scans Nifty 50 via technical analysis
├── Analyst Agent — deep-dives news/sentiment on flagged stocks
└── Executor Agent — validates risk limits, places orders
```

## MCP Servers Available

### angel-one-mcp
Market data and order execution. Tools: `login_session`, `get_live_quote`, `get_historical_candles`, `get_watchlist_quotes`, `place_order`, `get_order_status`, `cancel_order`, `get_positions`, `get_nifty50_symbols`, `refresh_session`

### portfolio-db-mcp
Portfolio state, trade journaling, risk enforcement. Tools: `initialize_portfolio`, `get_portfolio_state`, `check_risk_limits`, `log_trade`, `update_position`, `get_daily_pnl`, `get_risk_metrics`, `get_trade_history`, `save_analysis`, `get_previous_analysis`

### news-sentiment-mcp
News and market sentiment data. Tools: `get_stock_news`, `get_market_news`, `get_fii_dii_data`, `get_corporate_actions`, `get_india_vix`, `get_sector_performance`

## Trading Cycle (repeat every 5-10 minutes during market hours)

1. **Pre-check** (Lead): Call `get_portfolio_state`, `get_daily_pnl`, `get_risk_metrics`. If circuit breaker hit → STOP.
2. **Screen** (Screener): Get Nifty 50 symbols → fetch candles → compute RSI/MACD/EMA → flag stocks with score ≥ 60.
3. **Analyze** (Analyst): For flagged stocks → fetch news → score sentiment → check for red flags.
4. **Decide** (Lead): Synthesize technical + sentiment. Apply decision matrix:
   - ALL pass (tech ≥60, sentiment OK, no red flags, capacity) → EXECUTE
   - 3 of 4 → PROCEED WITH CAUTION (75% position)
   - ≤2 → SKIP
5. **Execute** (Executor): Call `check_risk_limits` FIRST. If approved → `place_order` → `log_trade` → `update_position`.
6. **Monitor** (Executor): Check existing positions against stop-losses.
7. **Log** (Lead): Summarize cycle with decisions and reasoning.

## Decision Thresholds
- Technical score ≥ 60 to flag for analysis
- Sentiment must not be BEARISH (veto override)
- Red flags = AUTOMATIC VETO regardless of technical score
- Confidence: HIGH (tech≥75 + bullish) = 100% position, MODERATE = 75%, LOW = 50%

## IMMUTABLE SAFETY RULES
These rules are enforced in MCP server CODE. You cannot override them:

1. **Market hours only**: Orders blocked outside 9:30-15:15 IST
2. **Max 10% per stock**: Position size hard-capped at 10% of capital
3. **Max 5 positions**: No new BUYs when 5 positions open
4. **Stop-loss REQUIRED**: Every BUY must have stop-loss (3-5% from entry)
5. **Daily loss limit 2%**: Circuit breaker halts ALL trading when hit
6. **No duplicate positions**: Can't buy a stock you already hold
7. **Trade journaling**: Every trade logged with full reasoning

## Critical Rules for Agents
- The Lead NEVER places orders directly. Only the Executor does.
- The Executor ALWAYS calls `check_risk_limits` before `place_order`.
- Every trade MUST be logged with `log_trade` including reasoning.
- If `check_risk_limits` returns `approved: false`, DO NOT proceed.
- When in doubt, DO NOT TRADE. Missing a trade is always better than a bad trade.

## File Structure
```
trading-agent/
├── .claude/settings.json     # Agent teams enabled
├── .mcp.json                 # MCP server config
├── CLAUDE.md                 # This file
├── mcp-servers/
│   ├── shared/__init__.py    # Config, constants, risk limits
│   ├── angel-one-mcp/        # Market data & orders
│   ├── portfolio-db-mcp/     # Portfolio & risk management
│   └── news-sentiment-mcp/   # News & sentiment
├── data/                     # SQLite databases (auto-created)
└── requirements.txt          # Python dependencies
```

## Getting Started
1. `pip install -r requirements.txt`
2. Fill in `.mcp.json` env vars with Angel One credentials
3. Run `claude` in this directory
4. Call `initialize_portfolio` to set up the database
5. Call `login_session` to authenticate with Angel One
6. Begin trading cycle
