"""
Check if the Indian stock market is currently in active trading hours.
Uses IST (Asia/Kolkata) timezone.
"""

from datetime import datetime, time
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)
ACTIVE_START = time(9, 30)
ACTIVE_END = time(15, 15)


def is_market_open() -> bool:
    """Check if NSE is in regular session (9:15-15:30 IST)."""
    now = datetime.now(IST)
    if now.weekday() >= 5:  # Saturday/Sunday
        return False
    return MARKET_OPEN <= now.time() <= MARKET_CLOSE


def is_active_trading_window() -> bool:
    """Check if within our active trading window (9:30-15:15 IST)."""
    now = datetime.now(IST)
    if now.weekday() >= 5:
        return False
    return ACTIVE_START <= now.time() <= ACTIVE_END


def get_market_status() -> dict:
    """Return current market status with details."""
    now = datetime.now(IST)
    current_time = now.time()
    weekday = now.weekday()

    if weekday >= 5:
        status = "CLOSED"
        reason = "Weekend"
    elif current_time < MARKET_OPEN:
        status = "PRE_MARKET"
        reason = f"Market opens at {MARKET_OPEN}"
    elif current_time < ACTIVE_START:
        status = "OPENING_AUCTION"
        reason = "Opening auction in progress, avoid trading"
    elif current_time <= ACTIVE_END:
        status = "ACTIVE"
        reason = "Active trading window"
    elif current_time <= MARKET_CLOSE:
        status = "CLOSING"
        reason = "Closing period, avoid new trades"
    else:
        status = "CLOSED"
        reason = "Market closed for the day"

    return {
        "status": status,
        "current_time_ist": now.isoformat(),
        "is_trading_allowed": status == "ACTIVE",
        "reason": reason,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_market_status(), indent=2))
