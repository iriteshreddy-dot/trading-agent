# Multi-Agent Trading System — Project Plan

## Architecture: Claude Code Agent Teams + Custom Skills + MCP Tools

### The Vision

Transform your existing single-loop trading agent into a **multi-agent system** where Claude Code acts as the orchestrator (Team Lead), spawning specialized teammates that work in parallel — each with their own context window, tools, and expertise.

```
┌──────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (Team Lead)                       │
│         Claude Code session in delegate mode                     │
│         Coordinates all agents, synthesizes decisions             │
│         Runs on: Opus 4.6 (best reasoning for coordination)      │
└────────┬──────────────┬──────────────────┬───────────────────────┘
         │              │                  │
    ┌────▼────┐   ┌─────▼─────┐    ┌──────▼──────┐
    │SCREENER │   │ ANALYST   │    │  EXECUTOR   │
    │Teammate │   │ Teammate  │    │  Teammate   │
    │         │   │           │    │             │
    │Scans    │   │Deep dives │    │Executes     │
    │Nifty 50 │   │on flagged │    │trades,      │
    │for      │   │stocks -   │    │manages      │
    │signals  │   │sentiment, │    │portfolio,   │
    │via TA   │   │fundament- │    │enforces     │
    │         │   │als, news  │    │risk rules   │
    │Sonnet   │   │           │    │             │
    │(cheaper)│   │Opus/Sonnet│    │Sonnet       │
    └─────────┘   └───────────┘    └─────────────┘
         │              │                  │
    ┌────▼────┐   ┌─────▼─────┐    ┌──────▼──────┐
    │market-  │   │analysis-  │    │trading-     │
    │data     │   │engine     │    │execution    │
    │SKILL    │   │SKILL      │    │SKILL        │
    └─────────┘   └───────────┘    └─────────────┘
         │              │                  │
    ┌────▼────────────▼──────────────▼────┐
    │         MCP SERVERS (Tools)          │
    │  Angel One API │ SQLite DB │ News   │
    └─────────────────────────────────────┘
```

---

## Phase 1: Skills to Build

Skills are the knowledge layer — they tell each agent HOW to do its job. MCP servers are the action layer — they let agents actually DO things.

### Skill 1: `market-data-skill`

**Purpose:** Teaches Claude how to fetch, interpret, and work with Indian market data via Angel One SmartAPI.

```
.claude/skills/market-data/
├── SKILL.md                    # Core instructions
├── references/
│   ├── angel-one-api.md        # Angel One SmartAPI endpoints, auth, rate limits
│   ├── nifty50-symbols.md      # Symbol mapping table (NSE symbols → Angel One tokens)
│   └── market-hours.md         # IST trading hours, pre-market, holidays
└── scripts/
    ├── fetch_live_price.py     # Get LTP for a symbol
    ├── fetch_historical.py     # Get OHLCV candles
    └── check_market_status.py  # Is market open right now?
```

**SKILL.md content outline:**
- When to use: Any time market data is needed for Indian stocks
- How Angel One auth works (session token refresh)
- Symbol format conventions (NSE:RELIANCE, BSE:500325)
- Rate limit awareness (don't hammer the API)
- Data freshness expectations (15-min delay on free tier vs live)
- Error handling patterns (session expired, market closed, symbol not found)

---

### Skill 2: `technical-analysis-skill`

**Purpose:** Teaches Claude how to compute and interpret technical indicators for Indian stocks.

```
.claude/skills/technical-analysis/
├── SKILL.md                        # Core TA instructions
├── references/
│   ├── indicators.md               # RSI, MACD, Bollinger, MAs — formulas + interpretation
│   ├── signal-patterns.md          # Bullish/bearish patterns and what they mean
│   └── indian-market-context.md    # Nifty-specific patterns, sector rotation, FII/DII flows
└── scripts/
    ├── compute_indicators.py       # Takes OHLCV data, returns all indicators
    ├── score_signal_strength.py    # Composite signal scoring (0-100)
    └── detect_patterns.py          # Chart pattern detection
```

**SKILL.md content outline:**
- When to use: Analyzing stocks for technical trading signals
- Indicator definitions with interpretation rules:
  - RSI: <30 oversold, >70 overbought, divergence detection
  - MACD: Signal line crossovers, histogram momentum
  - Moving Averages: 20/50/200 EMA, golden/death cross
  - Bollinger Bands: Squeeze detection, band walks
  - Volume: Confirmation rules, unusual volume flags
- Composite scoring methodology
- Indian market nuances (circuit limits, T+1 settlement, expiry day effects)
- Signal confidence levels: STRONG / MODERATE / WEAK / NO SIGNAL

---

### Skill 3: `sentiment-analysis-skill`

**Purpose:** Teaches Claude how to gather and score market sentiment from news sources.

```
.claude/skills/sentiment-analysis/
├── SKILL.md                        # Sentiment analysis instructions
├── references/
│   ├── news-sources.md             # Indian financial news APIs/sources
│   ├── sentiment-scoring.md        # How to score headlines and articles
│   └── market-impact-patterns.md   # How different news types affect stocks
└── scripts/
    ├── fetch_news.py               # Fetch headlines for a stock/sector
    ├── score_sentiment.py          # LLM-based sentiment scoring
    └── aggregate_sentiment.py      # Combine multiple sources into a single score
```

**SKILL.md content outline:**
- When to use: Evaluating news/sentiment before making trade decisions
- News source priority (MoneyControl, ET Markets, LiveMint, BSE/NSE announcements)
- Sentiment classification: BULLISH / BEARISH / NEUTRAL with confidence
- Corporate action detection (earnings, dividends, splits, buybacks)
- Sector-level sentiment (Banking, IT, Pharma, Auto)
- FII/DII flow interpretation
- Time-decay on news (breaking vs 24h old vs stale)

---

### Skill 4: `portfolio-management-skill`

**Purpose:** Teaches Claude how to manage positions, track P&L, and enforce risk rules.

```
.claude/skills/portfolio-management/
├── SKILL.md                        # Portfolio management rules
├── references/
│   ├── risk-rules.md               # Position sizing, max exposure, stop-loss rules
│   ├── portfolio-schema.md         # SQLite table schemas
│   └── trade-journal-format.md     # How to log trades and reasoning
└── scripts/
    ├── get_portfolio_state.py      # Current holdings, cash, P&L
    ├── calculate_position_size.py  # Kelly criterion / fixed fractional
    ├── check_risk_limits.py        # Validate trade against all risk rules
    └── log_trade.py                # Write to trade journal
```

**SKILL.md content outline:**
- When to use: Before/after any trade execution, portfolio review
- Risk rules (HARD LIMITS — these override any LLM decision):
  - Max 10% of capital in any single stock
  - Max 5 open positions at a time
  - Daily loss limit: 2% of total capital
  - Always set stop-loss at entry (default: 3% below entry)
  - No trading in first 15 min or last 15 min of session
- Position sizing calculation methodology
- P&L tracking (realized vs unrealized)
- Trade journal requirements (every trade must log: reasoning, indicators, sentiment, confidence)
- Portfolio rebalancing triggers

---

### Skill 5: `trading-orchestrator-skill`

**Purpose:** The master skill that the Team Lead uses to coordinate the multi-agent workflow.

```
.claude/skills/trading-orchestrator/
├── SKILL.md                        # Orchestration instructions
├── references/
│   ├── agent-roles.md              # What each teammate does
│   ├── decision-framework.md       # How to synthesize inputs into decisions
│   ├── cycle-template.md           # Template for each trading cycle
│   └── escalation-rules.md         # When to alert the human operator
└── scripts/
    ├── run_trading_cycle.py        # Orchestrate one complete cycle
    ├── generate_daily_report.py    # End-of-day summary
    └── check_market_calendar.py    # Holidays, special sessions
```

**SKILL.md content outline:**
- When to use: Running the trading system, coordinating agents
- Trading cycle definition:
  1. Pre-market: Check market calendar, refresh API session
  2. Screening: Screener teammate scans watchlist
  3. Analysis: Analyst teammate deep-dives flagged stocks
  4. Decision: Lead synthesizes all inputs, applies decision framework
  5. Execution: Executor teammate places orders (with risk checks)
  6. Monitoring: Track open positions, adjust stops
  7. Post-market: Generate daily report, update trade journal
- Decision framework:
  - STRONG BUY: Technical signal strong + Sentiment bullish + Fundamentals support
  - BUY: 2 out of 3 aligned, no red flags
  - HOLD: Mixed signals, wait for clarity
  - SELL: Stop-loss triggered OR reversal signals
- Escalation: Alert human via Telegram for any trade >5% of capital

---

## Phase 2: MCP Servers to Build

MCP servers are the actual tools. Skills teach Claude WHAT to do; MCP servers let Claude DO it.

### MCP Server 1: `angel-one-mcp`

```
Tools exposed:
├── get_live_quote(symbol)              → LTP, bid/ask, volume
├── get_historical_candles(symbol,      → OHLCV array
│   interval, from_date, to_date)
├── get_watchlist_quotes()              → Batch prices for Nifty 50
├── place_order(symbol, side,           → Order ID
│   quantity, price, order_type)
├── get_order_status(order_id)          → Status, fill price
├── cancel_order(order_id)             → Confirmation
├── get_positions()                    → Current open positions
└── refresh_session()                  → Refresh auth token
```

### MCP Server 2: `portfolio-db-mcp`

```
Tools exposed:
├── get_portfolio_state()               → Holdings, cash, total P&L
├── get_trade_history(days)             → Recent trades with reasoning
├── log_trade(trade_data)              → Write trade to journal
├── get_previous_analysis(symbol)       → Last analysis for a stock
├── update_position(symbol, data)       → Update stop-loss, target
├── get_daily_pnl()                    → Today's P&L breakdown
└── get_risk_metrics()                 → Current exposure, drawdown
```

### MCP Server 3: `news-sentiment-mcp`

```
Tools exposed:
├── get_stock_news(symbol, hours)       → Recent headlines
├── get_sector_news(sector)            → Sector-level news
├── get_market_news()                  → Broad market news
├── get_fii_dii_data()                → Foreign/Domestic fund flows
└── get_corporate_actions(symbol)      → Upcoming events
```

---

## Phase 3: Project Structure

```
trading-agent/
├── .claude/
│   ├── skills/
│   │   ├── market-data/
│   │   │   ├── SKILL.md
│   │   │   ├── references/
│   │   │   └── scripts/
│   │   ├── technical-analysis/
│   │   │   ├── SKILL.md
│   │   │   ├── references/
│   │   │   └── scripts/
│   │   ├── sentiment-analysis/
│   │   │   ├── SKILL.md
│   │   │   ├── references/
│   │   │   └── scripts/
│   │   ├── portfolio-management/
│   │   │   ├── SKILL.md
│   │   │   ├── references/
│   │   │   └── scripts/
│   │   └── trading-orchestrator/
│   │       ├── SKILL.md
│   │       ├── references/
│   │       └── scripts/
│   └── settings.json               # Agent teams enabled, permissions
├── mcp-servers/
│   ├── angel-one-mcp/
│   │   ├── src/
│   │   ├── package.json
│   │   └── README.md
│   ├── portfolio-db-mcp/
│   │   ├── src/
│   │   ├── package.json
│   │   └── README.md
│   └── news-sentiment-mcp/
│       ├── src/
│       ├── package.json
│       └── README.md
├── data/
│   ├── portfolio.db                # SQLite database
│   ├── trade_journal.db            # Trade history + reasoning
│   └── analysis_cache/             # Cached analysis results
├── orchestrator/
│   ├── run_trading_session.py      # External loop that drives Claude Code
│   ├── market_calendar.py          # Holiday/session checker
│   └── telegram_alerts.py          # Alert notifications
├── CLAUDE.md                       # Project-level instructions
├── .mcp.json                       # MCP server configuration
└── README.md
```

---

## Phase 4: CLAUDE.md (The Brain of the Whole System)

This is critical — every teammate reads CLAUDE.md, so it sets the rules for the entire system.

```markdown
# Trading Agent System

## Identity
You are a multi-agent trading system for the Indian stock market (NSE).
You trade Nifty 50 stocks using a combination of technical analysis, 
sentiment analysis, and fundamental screening.

## Capital & Risk Rules (IMMUTABLE — NEVER OVERRIDE)
- Starting capital: ₹1,00,000
- Max position size: 10% of current capital per stock
- Max open positions: 5
- Daily loss limit: 2% of total capital (stop ALL trading if hit)
- Every position MUST have a stop-loss set at entry
- Default stop-loss: 3% below entry price
- No trading in first 15 min (9:15-9:30) or last 15 min (3:15-3:30)

## Decision Framework
A trade requires:
- Technical signal strength ≥ 60/100
- No negative sentiment red flags
- Portfolio risk check passed
- At least 2 of 3 analysis dimensions aligned

## Agent Roles
- Team Lead (Orchestrator): Coordinates cycles, synthesizes decisions, 
  NEVER executes trades directly
- Screener: Scans watchlist using technical-analysis-skill, flags candidates
- Analyst: Deep-dives flagged stocks using sentiment + fundamentals
- Executor: Places orders, manages positions, enforces risk limits

## Trading Hours
- Market: 9:15 AM - 3:30 PM IST
- Active trading: 9:30 AM - 3:15 PM IST
- Cycle frequency: Every 5 minutes during active hours

## MCP Servers Available
- angel-one-mcp: Market data and order execution
- portfolio-db-mcp: Portfolio state and trade journaling
- news-sentiment-mcp: News and sentiment data

## Logging
Every analysis cycle MUST be logged to portfolio-db-mcp.
Every trade MUST include: symbol, action, quantity, price, 
reasoning, indicator values, sentiment score, confidence level.
```

---

## Phase 5: How a Trading Cycle Works

### Step 1: Orchestrator starts a cycle
The external Python script calls Claude Code with the trading-orchestrator-skill.
The lead enters delegate mode (Shift+Tab).

### Step 2: Screener teammate activates
- Loads market-data-skill and technical-analysis-skill
- Fetches live prices for Nifty 50 via angel-one-mcp
- Computes RSI, MACD, MAs for each stock
- Scores signal strength (0-100)
- Messages lead: "3 stocks flagged: RELIANCE (score: 78), INFY (72), HDFCBANK (65)"

### Step 3: Analyst teammate activates (triggered by screener results)
- Loads sentiment-analysis-skill
- For each flagged stock:
  - Fetches recent news via news-sentiment-mcp
  - Scores sentiment (BULLISH/BEARISH/NEUTRAL)
  - Checks corporate actions calendar
  - Checks FII/DII sector flows
- Messages lead: "RELIANCE: Bullish sentiment (earnings beat), 
  INFY: Neutral (no news), HDFCBANK: Bearish (NPA concerns)"

### Step 4: Lead synthesizes
- Receives screener + analyst reports
- Applies decision framework from CLAUDE.md
- Decision: BUY RELIANCE (tech strong + sentiment bullish)
- Decision: HOLD INFY (mixed signals)
- Decision: SKIP HDFCBANK (sentiment red flag)

### Step 5: Executor teammate activates
- Loads portfolio-management-skill
- Runs risk check via portfolio-db-mcp:
  - Current exposure: 35% (OK, under limit)
  - Position size for RELIANCE: ₹10,000 (10% of capital)
  - Daily P&L: +0.5% (OK, under loss limit)
- Places order via angel-one-mcp
- Sets stop-loss
- Logs trade to portfolio-db-mcp with full reasoning

### Step 6: Lead generates cycle summary
- Writes to analysis log
- If any position hit stop-loss → alert via Telegram
- Waits 5 minutes → next cycle

---

## Phase 6: Implementation Roadmap

### Week 1-2: Foundation
- [ ] Set up project structure
- [ ] Build the 3 MCP servers (angel-one, portfolio-db, news-sentiment)
- [ ] Test each MCP server independently
- [ ] Create SQLite database schema

### Week 3-4: Skills Creation
- [ ] Write market-data-skill with Angel One reference docs
- [ ] Write technical-analysis-skill with indicator formulas
- [ ] Write sentiment-analysis-skill with news source configs
- [ ] Write portfolio-management-skill with risk rules
- [ ] Write trading-orchestrator-skill with cycle definitions
- [ ] Test each skill independently via Claude Code

### Week 5-6: Agent Teams Integration
- [ ] Enable agent teams in settings.json
- [ ] Configure CLAUDE.md with all system rules
- [ ] Test multi-agent cycle with paper trading
- [ ] Build external orchestrator (Python loop)
- [ ] Add Telegram alerting

### Week 7-8: Testing & Refinement
- [ ] Run paper trading for 2 full weeks
- [ ] Analyze trade journal for quality of decisions
- [ ] Refine skills based on observed agent behavior
- [ ] Tune indicator thresholds and scoring
- [ ] Optimize cycle frequency and token usage

### Week 9+: Advanced
- [ ] Add tiered models (Sonnet for screener, Opus for decisions)
- [ ] Implement sector rotation analysis
- [ ] Add options/derivatives awareness
- [ ] Consider live trading with minimal capital

---

## Key Technical Notes

### Agent Teams Configuration
```json
// .claude/settings.json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

### Token Cost Awareness
Each teammate is a FULL Claude Code session (~5x cost of subagents).
For a 6-hour trading day at 5-min cycles = 72 cycles.
With 3 teammates per cycle = 216 agent sessions.
**Use Sonnet for screener/executor, Opus only for the lead's synthesis.**

### Session Management
Agent teams don't survive session restarts.
The external orchestrator handles crash recovery:
- If Claude Code session dies → restart with fresh team
- Portfolio state persists in SQLite (not in Claude's memory)
- Previous analysis persists in database

### Safety Guardrails (Defense in Depth)
Layer 1: CLAUDE.md rules (LLM-level, can be "convinced" to break)
Layer 2: Skill instructions (loaded into context, stronger)
Layer 3: MCP server code (hard-coded limits in Python, UNBREAKABLE)
Layer 4: External orchestrator (kills session if daily loss limit hit)

**The most critical risk rules live in Layer 3 and 4, NOT in the prompt.**
