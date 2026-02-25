"""
Position size calculator using fixed fractional method.

Risk per trade: 1% of current capital
Max position: 10% of current capital per stock
Always round DOWN (floor), never up.
"""

import math


# Risk constants (mirror shared/__init__.py)
MAX_POSITION_PCT = 0.10       # 10% of capital max per stock
RISK_PER_TRADE_PCT = 0.01    # 1% of capital risked per trade
DEFAULT_STOP_LOSS_PCT = 0.03  # 3% below entry
MAX_STOP_LOSS_PCT = 0.05     # 5% max stop-loss distance


def calculate_position_size(
    capital: float,
    entry_price: float,
    stop_loss_price: float,
    confidence: str = "HIGH",
) -> dict:
    """
    Calculate position size using fixed fractional method.

    Args:
        capital: Current available capital (not starting capital)
        entry_price: Expected entry price
        stop_loss_price: Stop-loss price level
        confidence: HIGH (100%), MODERATE (75%), LOW (50%)

    Returns:
        Dict with quantity, position_value, risk_amount, etc.
    """
    # Validate stop-loss distance
    sl_distance = entry_price - stop_loss_price
    sl_pct = sl_distance / entry_price

    if sl_pct < 0.015 or sl_pct > MAX_STOP_LOSS_PCT:
        return {
            "status": "error",
            "message": f"Stop-loss must be 1.5-5% below entry. Got: {sl_pct:.1%}",
        }

    # Step 1: Risk-based sizing
    risk_per_trade = capital * RISK_PER_TRADE_PCT
    risk_based_qty = risk_per_trade / sl_distance

    # Step 2: Max position cap
    max_position_value = capital * MAX_POSITION_PCT
    cap_based_qty = max_position_value / entry_price

    # Step 3: Take minimum and floor
    base_qty = math.floor(min(risk_based_qty, cap_based_qty))

    # Step 4: Apply confidence multiplier
    multipliers = {"HIGH": 1.0, "MODERATE": 0.75, "LOW": 0.50}
    multiplier = multipliers.get(confidence, 0.75)
    final_qty = max(1, math.floor(base_qty * multiplier))

    position_value = final_qty * entry_price
    risk_amount = final_qty * sl_distance
    position_pct = (position_value / capital) * 100

    return {
        "status": "ok",
        "quantity": final_qty,
        "entry_price": entry_price,
        "stop_loss": stop_loss_price,
        "position_value": round(position_value, 2),
        "position_pct_of_capital": round(position_pct, 2),
        "risk_amount": round(risk_amount, 2),
        "risk_pct_of_capital": round((risk_amount / capital) * 100, 2),
        "confidence": confidence,
        "multiplier_applied": multiplier,
    }


if __name__ == "__main__":
    import json

    result = calculate_position_size(
        capital=100000,
        entry_price=2500,
        stop_loss_price=2425,  # 3% below
        confidence="HIGH",
    )
    print(json.dumps(result, indent=2))
