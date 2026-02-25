"""
Trade journaling — format and log trades.
Stub — actual logging goes through the portfolio-db-mcp log_trade() tool.

Every trade MUST be logged with full reasoning context.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def format_trade_entry(
    symbol: str,
    token: str,
    transaction_type: str,
    quantity: int,
    price: float,
    order_id: str,
    technical_score: float,
    sentiment_score: float,
    sentiment_label: str,
    confidence: str,
    reasoning: str,
    indicators_json: str,
    stop_loss: float,
    capital: float,
) -> dict:
    """
    Format a trade entry for journaling.

    This is the format expected by portfolio-db-mcp log_trade() tool.
    """
    now = datetime.now(IST)
    trade_id = f"T{now.strftime('%Y%m%d%H%M%S')}_{symbol.replace('-EQ', '')}"
    position_value = quantity * price
    risk_amount = quantity * (price - stop_loss) if transaction_type == "BUY" else 0

    return {
        "trade_id": trade_id,
        "symbol": symbol,
        "token": token,
        "transaction_type": transaction_type,
        "quantity": quantity,
        "price": price,
        "order_id": order_id,
        "timestamp": now.isoformat(),
        "technical_score": technical_score,
        "sentiment_score": sentiment_score,
        "sentiment_label": sentiment_label,
        "confidence": confidence,
        "reasoning": reasoning,
        "indicators_json": indicators_json,
        "stop_loss": stop_loss,
        "position_value": round(position_value, 2),
        "risk_amount": round(risk_amount, 2),
        "capital_at_trade": capital,
    }


if __name__ == "__main__":
    import json

    entry = format_trade_entry(
        symbol="RELIANCE-EQ",
        token="2885",
        transaction_type="BUY",
        quantity=4,
        price=2500.00,
        order_id="ORD123456",
        technical_score=72,
        sentiment_score=65,
        sentiment_label="BULLISH",
        confidence="MODERATE",
        reasoning="RSI oversold + earnings beat + 50-EMA support",
        indicators_json='{"rsi": 32.5, "macd": "bullish_cross"}',
        stop_loss=2425.00,
        capital=100000,
    )
    print(json.dumps(entry, indent=2))
    print("\nUse portfolio-db-mcp log_trade() to persist this entry.")
