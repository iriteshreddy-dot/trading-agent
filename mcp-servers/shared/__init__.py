"""
Shared configuration and utilities for all MCP servers.
Credentials loaded from environment variables (set in .mcp.json env block).
"""

import os
from datetime import datetime, time
from zoneinfo import ZoneInfo

# ── Timezone ──────────────────────────────────────────────
IST = ZoneInfo("Asia/Kolkata")


def now_ist() -> datetime:
    return datetime.now(IST)


# ── Angel One Credentials (from env) ─────────────────────
ANGEL_API_KEY = os.environ.get("ANGEL_API_KEY", "")
ANGEL_CLIENT_ID = os.environ.get("ANGEL_CLIENT_ID", "")
ANGEL_PASSWORD = os.environ.get("ANGEL_PASSWORD", "")
ANGEL_TOTP_SECRET = os.environ.get("ANGEL_TOTP_SECRET", "")

# ── Database Paths ────────────────────────────────────────
PROJECT_ROOT = os.environ.get("TRADING_PROJECT_ROOT", os.path.expanduser("~/trading-agent"))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "portfolio.db")

# ── Trading Constants (IMMUTABLE RISK LIMITS) ─────────────
STARTING_CAPITAL = 100_000  # ₹1,00,000
MAX_POSITION_PCT = 0.10     # 10% of capital per stock
MAX_OPEN_POSITIONS = 5
DAILY_LOSS_LIMIT_PCT = 0.02  # 2% of capital = circuit breaker
DEFAULT_STOP_LOSS_PCT = 0.03  # 3% below entry
MAX_STOP_LOSS_PCT = 0.05     # absolute max 5%
RISK_PER_TRADE_PCT = 0.01    # 1% of capital risked per trade

# ── Market Hours ──────────────────────────────────────────
MARKET_OPEN = time(9, 15)     # NSE opens
MARKET_CLOSE = time(15, 30)   # NSE closes
ACTIVE_START = time(9, 30)    # Avoid first 15 min volatility
ACTIVE_END = time(15, 15)     # Avoid last 15 min volatility


def is_market_active() -> bool:
    """Check if current time is within active trading window."""
    current = now_ist().time()
    return ACTIVE_START <= current <= ACTIVE_END


def is_market_hours() -> bool:
    """Check if current time is within market hours (broader)."""
    current = now_ist().time()
    return MARKET_OPEN <= current <= MARKET_CLOSE


# ── Nifty 50 Symbols ─────────────────────────────────────
# Format: {symbol: token} - tokens from Angel One instrument master
# This gets populated at runtime by angel-one-mcp from instrument file
NIFTY50_SYMBOLS: dict[str, str] = {}
