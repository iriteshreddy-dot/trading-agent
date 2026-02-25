# Portfolio Database Schema

Database: SQLite with WAL mode, foreign keys enabled.
Path: `data/portfolio.db`

---

## Tables

### portfolio (Core portfolio state — single row)

```sql
CREATE TABLE portfolio (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    cash REAL NOT NULL,
    starting_capital REAL NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

- **Single row enforced** by `CHECK (id = 1)` constraint
- `cash` reflects available cash (starting capital minus invested capital plus realized P&L)
- `starting_capital` is set once at initialization (Rs.1,00,000) and never changes
- Timestamps stored as ISO 8601 strings with IST offset (+05:30)

---

### positions (Open and closed positions)

```sql
CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    token TEXT NOT NULL,
    exchange TEXT DEFAULT 'NSE',
    quantity INTEGER NOT NULL,
    entry_price REAL NOT NULL,
    stop_loss REAL NOT NULL,
    entry_time TEXT NOT NULL,
    trade_id TEXT,
    status TEXT DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'CLOSED')),
    exit_price REAL,
    exit_time TEXT,
    pnl REAL,
    UNIQUE(symbol, status)
);
```

- `token` is the Angel One instrument token (used for API calls)
- `trade_id` links to the `trades` table for the entry trade
- `UNIQUE(symbol, status)` prevents duplicate OPEN positions for the same stock
- When closed: `exit_price`, `exit_time`, and `pnl` are populated
- `pnl` = `(exit_price - entry_price) * quantity` for BUY positions

---

### trades (Full trade journal)

```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id TEXT UNIQUE NOT NULL,
    symbol TEXT NOT NULL,
    token TEXT NOT NULL,
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('BUY', 'SELL')),
    quantity INTEGER NOT NULL,
    price REAL NOT NULL,
    order_id TEXT,
    timestamp TEXT NOT NULL,
    technical_score REAL,
    sentiment_score REAL,
    sentiment_label TEXT,
    confidence TEXT CHECK (confidence IN ('HIGH', 'MODERATE', 'LOW')),
    reasoning TEXT,
    indicators_json TEXT,
    stop_loss REAL,
    position_value REAL,
    risk_amount REAL,
    capital_at_trade REAL
);
```

- `trade_id` format: `T{YYYYMMDD}_{sequence}` (e.g., T20260222_001)
- `order_id` is the Angel One order ID returned after placement
- `indicators_json` stores the technical indicators snapshot as JSON string
- `reasoning` is the human-readable trade rationale (required for audit)
- `position_value` = `price * quantity`
- `risk_amount` = `(price - stop_loss) * quantity` (max potential loss)
- `capital_at_trade` = portfolio cash at time of trade

---

### daily_pnl (Daily P&L tracking)

```sql
CREATE TABLE daily_pnl (
    date TEXT PRIMARY KEY,
    realized_pnl REAL DEFAULT 0,
    unrealized_pnl REAL DEFAULT 0,
    trades_count INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    circuit_breaker_hit INTEGER DEFAULT 0
);
```

- `date` format: `YYYY-MM-DD`
- `realized_pnl` updates when positions are closed
- `unrealized_pnl` updates during monitoring checks (mark-to-market)
- `circuit_breaker_hit` is 0 or 1; once set to 1, blocks new trades for the day
- A new row is auto-created for each trading day

---

### analysis_cache (Analysis cache with 30-min TTL)

```sql
CREATE TABLE analysis_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    analysis_type TEXT NOT NULL CHECK (analysis_type IN ('TECHNICAL', 'SENTIMENT', 'COMBINED')),
    score REAL,
    label TEXT,
    details_json TEXT,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
```

- TTL: 30 minutes from `created_at`
- `details_json` stores full analysis payload (indicators, news items, etc.)
- Queried via `get_previous_analysis()` to avoid redundant API calls
- Expired entries are ignored (not auto-deleted)

---

## Indices

```sql
CREATE INDEX idx_positions_status ON positions(status);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_timestamp ON trades(timestamp);
CREATE INDEX idx_analysis_cache_lookup ON analysis_cache(symbol, analysis_type);
```

---

## Key Relationships

```
portfolio (1 row)
    |
    +-- positions (0..5 OPEN, unlimited CLOSED)
    |       |
    |       +-- trades (1 BUY trade per position entry, 1 SELL trade per position exit)
    |
    +-- daily_pnl (1 row per trading day)
    |
    +-- analysis_cache (multiple per symbol, expires after 30 min)
```

---

## MCP Tool to Table Mapping

| MCP Tool | Primary Table(s) |
|---|---|
| `initialize_portfolio` | Creates all tables, inserts portfolio row |
| `get_portfolio_state` | Reads portfolio + positions (OPEN) |
| `check_risk_limits` | Reads portfolio, positions, daily_pnl |
| `log_trade` | Inserts into trades |
| `update_position` | Updates positions, daily_pnl, portfolio |
| `get_daily_pnl` | Reads daily_pnl |
| `get_risk_metrics` | Reads portfolio, positions, daily_pnl, trades |
| `get_trade_history` | Reads trades |
| `save_analysis` | Inserts into analysis_cache |
| `get_previous_analysis` | Reads analysis_cache (checks TTL) |
