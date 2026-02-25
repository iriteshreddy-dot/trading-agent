# Trading Agent System v1 — Complete Walkthrough

## What Is This?

A **paper trading bot** for Indian stocks (Nifty 50) that uses multiple AI agents working together to scan the market, analyze opportunities, and execute trades — all with simulated money (₹1,00,000). No real money is ever at risk.

Think of it like a trading desk with 4 people, each with a specific job, talking to each other through a coordinator.

---

## The Team

```
┌─────────────────────────────────────────────┐
│           TEAM LEAD (You/Opus 4.6)          │
│      Coordinates everything, makes the      │
│      final BUY/SELL/SKIP decisions.          │
│      NEVER touches data or orders directly.  │
└────────┬──────────┬──────────┬──────────────┘
         │          │          │
    ┌────▼───┐ ┌────▼───┐ ┌───▼──────┐
    │SCREENER│ │ANALYST │ │EXECUTOR  │
    │        │ │        │ │          │
    │Scans   │ │Checks  │ │Validates │
    │50 stocks│ │news &  │ │risk,     │
    │for     │ │sentiment│ │places    │
    │signals │ │for red  │ │orders,   │
    │(RSI,   │ │flags   │ │logs      │
    │MACD..) │ │        │ │trades    │
    └────────┘ └────────┘ └──────────┘
```

**Each agent has specific skills loaded:**
- **Screener** → `market-data` + `technical-analysis` skills
- **Analyst** → `sentiment-analysis` + `market-data` skills
- **Executor** → `portfolio-management` skill

---

## The Infrastructure (3 MCP Servers)

MCP servers are the "hands" — they let agents actually do things:

| Server | What It Does | Key Tools |
|--------|-------------|-----------|
| **angel-one-mcp** | Talks to Angel One broker API | `login_session`, `get_live_quote`, `get_historical_candles`, `get_watchlist_quotes`, `place_order`, `get_nifty50_symbols` |
| **portfolio-db-mcp** | SQLite database for portfolio tracking | `get_portfolio_state`, `check_risk_limits`, `log_trade`, `update_position`, `get_daily_pnl` |
| **news-sentiment-mcp** | Free news from Google RSS + NSE APIs | `get_stock_news`, `get_market_news`, `get_fii_dii_data`, `get_india_vix`, `get_sector_performance` |

---

## The Trading Cycle (Every 5-10 Minutes)

This is the core loop that runs during market hours (9:30 AM - 3:15 PM IST):

### Phase 1: Pre-Check (Lead)

```
"Is it safe to trade right now?"

→ get_portfolio_state()    — How much cash? How many positions open?
→ get_daily_pnl()          — Have we lost 2% today? (circuit breaker)
→ get_risk_metrics()       — Overall exposure dashboard

If circuit breaker hit → STOP. No trading for the rest of the day.
If market closed → STOP. Wait for next session.
```

### Phase 2: Screening (Screener Agent)

```
"Which stocks look interesting technically?"

→ get_nifty50_symbols()       — Get all 50 stocks
→ get_watchlist_quotes()      — Batch fetch current prices (1 API call!)
→ get_historical_candles()    — 50-day history for each interesting stock

Then compute for each stock:
  RSI (14)        → Is it oversold (<30) or overbought (>70)?
  MACD (12,26,9)  → Is momentum shifting?
  EMA (20/50/200) → What's the trend?
  Bollinger Bands → Is price at extremes?
  Volume          → Is there conviction behind the move?

Each stock gets a composite score: 0-100
Score ≥ 60 → "Hey Lead, check out RELIANCE (score: 78)"
Score < 60 → Ignored
```

### Phase 3: Analysis (Analyst Agent)

```
"Is there any news that changes the picture?"

Only runs if Screener flagged ≥ 1 stock.

For each flagged stock:
→ get_stock_news("RELIANCE")  — Recent headlines from Google News, ET
→ get_fii_dii_data()          — Are foreign investors buying or selling?
→ get_corporate_actions()      — Any dividends, splits coming up?
→ get_india_vix()             — How fearful is the market?

Score sentiment: -100 (strong bearish) to +100 (strong bullish)

RED FLAG CHECK (instant veto):
  - SEBI investigation?        → VETO
  - Auditor resigned?          → VETO
  - Promoter pledged >50%?     → VETO
  - Earnings missed by >20%?   → VETO

"Lead, RELIANCE sentiment is BULLISH (+65), no red flags."
```

### Phase 4: Decision (Lead)

```
"Should we trade this?"

The Lead applies a 4-criteria decision matrix:

  ┌─────────────────────────────────────┐
  │ 1. Technical score ≥ 60?    ✅      │
  │ 2. Sentiment not BEARISH?   ✅      │
  │ 3. No red flags?            ✅      │
  │ 4. Portfolio has capacity?  ✅      │
  │                                     │
  │ ALL 4 pass  → EXECUTE               │
  │ 3 of 4      → CAUTION (75% size)    │
  │ ≤ 2         → SKIP                  │
  └─────────────────────────────────────┘

Confidence determines position size:
  HIGH   (tech ≥75, sentiment bullish)  → 100% position
  MODERATE (tech 60-74, neutral/bullish) → 75% position
  LOW    (mixed signals)                → 50% position
```

### Phase 5: Execution (Executor Agent)

```
"Execute the trade safely."

STEP 1: check_risk_limits() — 8 hard checks, ALL must pass:
  □ Market open?
  □ Daily loss limit OK?
  □ Circuit breaker not hit?
  □ < 5 positions open?
  □ Not already holding this stock?
  □ Position ≤ 10% of capital (₹10,000)?
  □ Stop-loss 3-5% below entry?
  □ Enough cash?

  If ANY fails → REJECTED. Do not proceed. Period.

STEP 2: place_order()
  → BUY 4 shares of RELIANCE at ₹2,500
  → Stop-loss at ₹2,425 (3% below)
  → Order type: MARKET

STEP 3: log_trade()
  → Record everything: price, quantity, indicators, sentiment,
    confidence, reasoning, risk metrics

STEP 4: update_position()
  → Deduct ₹10,000 from cash
  → Add RELIANCE to open positions
```

### Phase 6: Monitoring (Executor Agent)

```
"Are our existing positions OK?"

For each open position:
→ Fetch current price
→ Is price within 0.5% of stop-loss? → ALERT
→ Is price >2% above entry? → Trail stop to breakeven
→ Did stop-loss trigger? → SELL immediately, log exit
```

### Phase 7: Summary (Lead)

```
Log the cycle:
  "Cycle C20260223_001: Scanned 50 stocks, flagged 3,
   analyzed 3, bought RELIANCE (score 78, bullish sentiment),
   skipped INFY (neutral sentiment), skipped HDFCBANK (bearish).
   Open positions: 3. Daily P&L: +0.5%"

Wait 5-10 minutes → Repeat from Phase 1
```

---

## The Safety Net (4 Layers)

This is what makes the system safe. Risk rules are enforced at multiple levels:

```
Layer 1: CLAUDE.md rules
  └─ LLM reads these, but could theoretically be "convinced" to ignore
      ↓
Layer 2: Skill instructions (.claude/skills/*/SKILL.md)
  └─ Loaded into agent context, stronger than Layer 1
      ↓
Layer 3: MCP server Python code ← THE REAL ENFORCEMENT
  └─ Hard-coded if/else checks. LLM literally CANNOT bypass these.
  └─ place_order() rejects if no stop-loss, wrong hours, size too big
  └─ check_risk_limits() rejects if ANY of 8 checks fail
  └─ Database UNIQUE constraint prevents duplicate positions
      ↓
Layer 4: Database constraints
  └─ SQLite enforces data integrity even if code has bugs
```

**The key insight:** The most critical rules live in Python code (Layer 3), not in prompts. Even if the AI hallucinates or gets confused, the MCP server will reject bad trades.

---

## Immutable Risk Rules

| Rule | Limit | Enforced In |
|------|-------|-------------|
| Market hours only | 9:30 AM - 3:15 PM IST | `angel-one-mcp` + `portfolio-db-mcp` |
| Max per stock | 10% of capital (₹10,000) | `angel-one-mcp` + `portfolio-db-mcp` |
| Max positions | 5 concurrent | `portfolio-db-mcp` |
| Stop-loss required | 3-5% below entry | `angel-one-mcp` |
| Daily loss circuit breaker | 2% of capital (₹2,000) | `portfolio-db-mcp` |
| No duplicate positions | 1 per stock | `portfolio-db-mcp` + SQLite UNIQUE |
| Trade journaling | Every trade logged | `portfolio-db-mcp` |

---

## Money Flow Example

```
Start: ₹1,00,000 cash, 0 positions

Cycle 1: BUY 4 RELIANCE @ ₹2,500 (₹10,000)
  Cash: ₹90,000 | Positions: 1 | Invested: ₹10,000

Cycle 5: BUY 3 TCS @ ₹3,300 (₹9,900)
  Cash: ₹80,100 | Positions: 2 | Invested: ₹19,900

Cycle 12: RELIANCE hits target → SELL @ ₹2,650
  P&L: +₹600 (4 × ₹150)
  Cash: ₹90,700 | Positions: 1 | Invested: ₹9,900

Cycle 20: TCS hits stop-loss → SELL @ ₹3,201
  P&L: -₹297 (3 × ₹99)
  Cash: ₹100,303 | Positions: 0 | Net: +₹303
```

---

## File Map

```
Trading-agent 2.0/
├── CLAUDE.md                          ← System rules (Layer 1)
├── .mcp.json                          ← MCP server config + credentials
├── requirements.txt                   ← Python dependencies
│
├── .claude/
│   ├── settings.json                  ← Agent teams enabled
│   └── skills/                        ← 5 skills (Layer 2)
│       ├── market-data/               ← How to fetch prices
│       ├── technical-analysis/        ← How to compute RSI/MACD/EMA
│       ├── sentiment-analysis/        ← How to score news
│       ├── portfolio-management/      ← Risk rules & position sizing
│       └── trading-orchestrator/      ← How to run the cycle
│
├── server.py                          ← Angel One MCP (Layer 3)
├── mnt/.../portfolio-db-mcp/server.py ← Portfolio MCP (Layer 3)
├── mnt/.../news-sentiment-mcp/server.py ← News MCP (Layer 3)
│
└── data/
    └── portfolio.db                   ← SQLite database (Layer 4)
```

---

## Getting Started

1. `pip install -r requirements.txt`
2. Copy `.mcp.json.example` → `.mcp.json`, fill in Angel One credentials
3. Run `claude` in this directory
4. Call `initialize_portfolio` → sets up the database
5. Call `login_session` → authenticates with Angel One
6. Say "Run a trading cycle" → the orchestrator takes over

The system handles everything from there — scanning, analyzing, deciding, executing, and logging — all while keeping your simulated capital safe behind multiple layers of risk enforcement.
