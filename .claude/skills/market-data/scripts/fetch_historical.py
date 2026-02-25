"""
Fetch historical OHLCV candles via Angel One SmartAPI.
Stub — actual execution goes through the angel-one-mcp MCP server.

Usage:
    This script demonstrates the expected data flow.
    In production, use the get_historical_candles() MCP tool instead.
"""


def fetch_historical(
    symbol_token: str,
    interval: str = "FIVE_MINUTE",
    days_back: int = 5,
    exchange: str = "NSE",
) -> list[list]:
    """
    Fetch OHLCV candles for technical analysis.

    Args:
        symbol_token: Angel One token e.g. "2885"
        interval: ONE_MINUTE, FIVE_MINUTE, FIFTEEN_MINUTE, ONE_HOUR, ONE_DAY
        days_back: Number of days of history (max 60 intraday, 2000 daily)
        exchange: "NSE" or "BSE"

    Returns:
        List of [timestamp, open, high, low, close, volume]
    """
    raise NotImplementedError(
        "Use the angel-one-mcp get_historical_candles() tool instead. "
        "This script is a reference stub."
    )


if __name__ == "__main__":
    print("This is a stub. Use the angel-one-mcp get_historical_candles() MCP tool.")
    print("Example: get_historical_candles(symbol_token='2885', interval='ONE_DAY', days_back=50)")
