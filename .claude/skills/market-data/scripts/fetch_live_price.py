"""
Fetch live price for a symbol via Angel One SmartAPI.
Stub — actual execution goes through the angel-one-mcp MCP server.

Usage:
    This script demonstrates the expected data flow.
    In production, use the get_live_quote() MCP tool instead.
"""


def fetch_live_price(symbol: str, token: str, exchange: str = "NSE") -> dict:
    """
    Fetch current LTP and OHLCV for a symbol.

    Args:
        symbol: Trading symbol e.g. "RELIANCE-EQ"
        token: Angel One token e.g. "2885"
        exchange: "NSE" or "BSE"

    Returns:
        dict with ltp, open, high, low, close, volume, timestamp
    """
    # In production, this calls the angel-one-mcp get_live_quote tool.
    # This stub shows the expected interface.
    raise NotImplementedError(
        "Use the angel-one-mcp get_live_quote() tool instead. "
        "This script is a reference stub."
    )


if __name__ == "__main__":
    print("This is a stub. Use the angel-one-mcp get_live_quote() MCP tool.")
    print("Example: get_live_quote(symbol='RELIANCE-EQ', token='2885')")
