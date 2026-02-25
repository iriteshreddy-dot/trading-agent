"""
Market calendar checker for Indian stock market.
Checks for holidays, special sessions, and trading day status.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

# NSE holidays for 2026 (update annually from NSE circular)
# Source: https://www.nseindia.com/resources/exchange-communication-holidays
NSE_HOLIDAYS_2026 = [
    date(2026, 1, 26),   # Republic Day
    date(2026, 3, 17),   # Holi
    date(2026, 3, 30),   # Id-Ul-Fitr (tentative)
    date(2026, 4, 2),    # Ram Navami
    date(2026, 4, 3),    # Good Friday
    date(2026, 4, 14),   # Dr. Ambedkar Jayanti
    date(2026, 5, 1),    # Maharashtra Day
    date(2026, 6, 5),    # Id-Ul-Adha (tentative)
    date(2026, 7, 6),    # Muharram (tentative)
    date(2026, 8, 15),   # Independence Day
    date(2026, 8, 19),   # Janmashtami
    date(2026, 10, 2),   # Mahatma Gandhi Jayanti
    date(2026, 10, 20),  # Diwali (Laxmi Pujan)
    date(2026, 10, 21),  # Diwali (Balipratipada)
    date(2026, 11, 5),   # Guru Nanak Jayanti
    date(2026, 12, 25),  # Christmas
]

# Special trading days (e.g., Muhurat trading on Diwali)
SPECIAL_SESSIONS_2026 = [
    {
        "date": date(2026, 10, 20),
        "name": "Muhurat Trading",
        "start": "18:15",
        "end": "19:15",
        "notes": "Special Diwali session, symbolic trading only",
    },
]


def is_trading_day(check_date: date | None = None) -> dict:
    """
    Check if a given date is a trading day.

    Returns:
        {is_trading_day: bool, reason: str, special_session: dict|None}
    """
    if check_date is None:
        check_date = datetime.now(IST).date()

    # Weekend check
    if check_date.weekday() >= 5:
        return {
            "is_trading_day": False,
            "reason": "Weekend" if check_date.weekday() == 5 else "Sunday",
            "special_session": None,
        }

    # Holiday check
    if check_date in NSE_HOLIDAYS_2026:
        # Check for special sessions
        special = None
        for session in SPECIAL_SESSIONS_2026:
            if session["date"] == check_date:
                special = session
                break

        return {
            "is_trading_day": False,
            "reason": "NSE Holiday",
            "special_session": special,
        }

    return {
        "is_trading_day": True,
        "reason": "Regular trading day",
        "special_session": None,
    }


def is_expiry_day(check_date: date | None = None) -> bool:
    """Check if today is weekly options expiry (Thursday)."""
    if check_date is None:
        check_date = datetime.now(IST).date()
    return check_date.weekday() == 3  # Thursday


def get_next_trading_day(from_date: date | None = None) -> date:
    """Find the next valid trading day."""
    if from_date is None:
        from_date = datetime.now(IST).date()

    from datetime import timedelta
    check = from_date + timedelta(days=1)
    while True:
        result = is_trading_day(check)
        if result["is_trading_day"]:
            return check
        check += timedelta(days=1)


if __name__ == "__main__":
    import json

    today = datetime.now(IST).date()
    result = is_trading_day(today)
    result["date"] = str(today)
    result["is_expiry_day"] = is_expiry_day(today)
    result["next_trading_day"] = str(get_next_trading_day(today))

    # Make special_session serializable
    if result["special_session"]:
        result["special_session"]["date"] = str(result["special_session"]["date"])

    print(json.dumps(result, indent=2))
