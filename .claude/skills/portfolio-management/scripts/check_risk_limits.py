"""
Pre-trade risk validation — all 8 checks must pass.
Mirrors the check_risk_limits() tool in portfolio-db-mcp.

In production, use the portfolio-db-mcp check_risk_limits() MCP tool.
This script documents the validation logic.
"""

from datetime import time
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
ACTIVE_START = time(9, 30)
ACTIVE_END = time(15, 15)
MAX_POSITION_PCT = 0.10
MAX_OPEN_POSITIONS = 5
DAILY_LOSS_LIMIT_PCT = 0.02
MAX_STOP_LOSS_PCT = 0.05


def check_risk_limits(
    symbol: str,
    quantity: int,
    entry_price: float,
    stop_loss: float,
    capital: float,
    cash: float,
    open_positions: list[str],
    daily_loss_pct: float,
    circuit_breaker_hit: bool,
    technical_score: float = 0,
    sentiment_veto: bool = False,
) -> dict:
    """
    Run all pre-trade risk checks.

    Returns:
        {approved: bool, checks: list[{check, passed, detail}]}
    """
    checks = []
    all_passed = True

    def add_check(name: str, passed: bool, detail: str):
        nonlocal all_passed
        checks.append({"check": name, "passed": passed, "detail": detail})
        if not passed:
            all_passed = False

    # 1. Market hours
    from datetime import datetime
    now = datetime.now(IST).time()
    in_window = ACTIVE_START <= now <= ACTIVE_END
    add_check("market_active", in_window,
              f"Current: {now}, Window: {ACTIVE_START}-{ACTIVE_END}")

    # 2. Daily loss limit
    add_check("daily_loss_limit", daily_loss_pct < DAILY_LOSS_LIMIT_PCT,
              f"Daily loss: {daily_loss_pct:.2%}, Limit: {DAILY_LOSS_LIMIT_PCT:.0%}")

    # 3. Circuit breaker
    add_check("circuit_breaker", not circuit_breaker_hit,
              "Circuit breaker active" if circuit_breaker_hit else "OK")

    # 4. Open positions
    add_check("max_positions", len(open_positions) < MAX_OPEN_POSITIONS,
              f"Open: {len(open_positions)}, Max: {MAX_OPEN_POSITIONS}")

    # 5. No duplicate
    add_check("no_duplicate", symbol not in open_positions,
              f"{'Already holding ' + symbol if symbol in open_positions else 'OK'}")

    # 6. Position size
    position_value = quantity * entry_price
    max_value = capital * MAX_POSITION_PCT
    add_check("position_size", position_value <= max_value,
              f"Value: ₹{position_value:,.0f}, Max: ₹{max_value:,.0f}")

    # 7. Stop-loss valid
    sl_pct = (entry_price - stop_loss) / entry_price
    add_check("stop_loss_valid", 0.015 <= sl_pct <= MAX_STOP_LOSS_PCT,
              f"SL distance: {sl_pct:.1%}, Range: 1.5%-5%")

    # 8. Sufficient cash
    add_check("sufficient_cash", cash >= position_value,
              f"Cash: ₹{cash:,.0f}, Required: ₹{position_value:,.0f}")

    return {
        "approved": all_passed,
        "checks": checks,
        "position_value": position_value,
        "risk_amount": quantity * (entry_price - stop_loss),
    }


if __name__ == "__main__":
    import json

    result = check_risk_limits(
        symbol="RELIANCE-EQ",
        quantity=4,
        entry_price=2500,
        stop_loss=2425,
        capital=100000,
        cash=65000,
        open_positions=["TCS-EQ", "INFY-EQ"],
        daily_loss_pct=0.005,
        circuit_breaker_hit=False,
    )
    print(json.dumps(result, indent=2))
