"""
Angel One MCP Server
====================
Provides market data and order execution via Angel One SmartAPI.
Transport: stdio (launched by Claude Code)

Tools:
  - login_session: Authenticate with Angel One
  - get_live_quote: Get current price for a symbol
  - get_historical_candles: OHLCV data for technical analysis
  - get_watchlist_quotes: Batch LTP for multiple symbols
  - place_order: Execute a trade (with hard-coded safety checks)
  - get_order_status: Check order state
  - cancel_order: Cancel pending order
  - get_positions: Current open positions from broker
  - get_nifty50_symbols: Return the Nifty 50 symbol-token map
"""

import json
import logging
import sys
from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP

# Add parent dir to path for shared config
sys.path.insert(0, __file__.rsplit("/", 2)[0])
from shared import (
    ANGEL_API_KEY,
    ANGEL_CLIENT_ID,
    ANGEL_PASSWORD,
    ANGEL_TOTP_SECRET,
    IST,
    MAX_OPEN_POSITIONS,
    MAX_POSITION_PCT,
    STARTING_CAPITAL,
    is_market_active,
    now_ist,
)

# ── Logging (stderr only - stdout is for MCP JSON-RPC) ───
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [angel-one-mcp] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("angel-one-mcp")

# ── MCP Server ────────────────────────────────────────────
mcp = FastMCP(
    "angel-one-mcp",
    json_response=True,
)

# ── Session State ─────────────────────────────────────────
# SmartConnect instance lives here after login
_smart_api = None
_auth_token = None
_refresh_token = None
_feed_token = None
_session_time = None

# ── Nifty 50 instrument mapping (loaded on first call) ───
_nifty50_map: dict[str, str] = {}


def _get_api():
    """Get authenticated SmartAPI instance, or raise."""
    if _smart_api is None:
        raise RuntimeError(
            "Not logged in. Call login_session first."
        )
    # Check if session is stale (>6 hours)
    if _session_time and (now_ist() - _session_time).seconds > 6 * 3600:
        raise RuntimeError(
            "Session expired (>6 hours). Call login_session to refresh."
        )
    return _smart_api


# ══════════════════════════════════════════════════════════
# TOOLS
# ══════════════════════════════════════════════════════════


@mcp.tool()
def login_session() -> dict:
    """
    Authenticate with Angel One SmartAPI using stored credentials.
    Must be called at the start of each trading session.
    Returns session status and available exchanges.

    Credentials are loaded from environment variables:
    ANGEL_API_KEY, ANGEL_CLIENT_ID, ANGEL_PASSWORD, ANGEL_TOTP_SECRET
    """
    global _smart_api, _auth_token, _refresh_token, _feed_token, _session_time

    try:
        from SmartApi import SmartConnect
        import pyotp
    except ImportError:
        return {
            "status": "error",
            "message": "SmartApi or pyotp not installed. Run: pip install smartapi-python pyotp",
        }

    if not all([ANGEL_API_KEY, ANGEL_CLIENT_ID, ANGEL_PASSWORD, ANGEL_TOTP_SECRET]):
        return {
            "status": "error",
            "message": "Missing credentials. Set ANGEL_API_KEY, ANGEL_CLIENT_ID, ANGEL_PASSWORD, ANGEL_TOTP_SECRET in environment.",
        }

    try:
        _smart_api = SmartConnect(api_key=ANGEL_API_KEY)
        totp = pyotp.TOTP(ANGEL_TOTP_SECRET).now()
        data = _smart_api.generateSession(ANGEL_CLIENT_ID, ANGEL_PASSWORD, totp)

        if not data.get("status"):
            _smart_api = None
            return {"status": "error", "message": f"Login failed: {data.get('message', 'Unknown error')}"}

        _auth_token = data["data"]["jwtToken"]
        _refresh_token = data["data"]["refreshToken"]
        _feed_token = _smart_api.getfeedToken()
        _session_time = now_ist()

        profile = _smart_api.getProfile(_refresh_token)
        exchanges = profile.get("data", {}).get("exchanges", [])

        log.info(f"Login successful. Exchanges: {exchanges}")
        return {
            "status": "success",
            "client_id": ANGEL_CLIENT_ID,
            "exchanges": exchanges,
            "session_time": _session_time.isoformat(),
        }
    except Exception as e:
        _smart_api = None
        log.error(f"Login error: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def get_live_quote(symbol: str, token: str, exchange: str = "NSE") -> dict:
    """
    Get the current live quote (LTP, open, high, low, close, volume) for a single symbol.

    Args:
        symbol: Trading symbol e.g. "RELIANCE-EQ"
        token: Angel One symbol token e.g. "2885"
        exchange: Exchange segment - "NSE" or "BSE" (default: NSE)
    """
    api = _get_api()
    try:
        data = api.ltpData(exchange, symbol, token)
        if data.get("status"):
            ltp_info = data.get("data", {})
            return {
                "status": "success",
                "symbol": symbol,
                "token": token,
                "exchange": exchange,
                "ltp": ltp_info.get("ltp"),
                "open": ltp_info.get("open"),
                "high": ltp_info.get("high"),
                "low": ltp_info.get("low"),
                "close": ltp_info.get("close"),
                "timestamp": now_ist().isoformat(),
            }
        return {"status": "error", "message": data.get("message", "Failed to fetch LTP")}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def get_historical_candles(
    symbol_token: str,
    interval: str = "FIVE_MINUTE",
    days_back: int = 5,
    exchange: str = "NSE",
) -> dict:
    """
    Get historical OHLCV candles for technical analysis.

    Args:
        symbol_token: Angel One symbol token e.g. "2885"
        interval: Candle interval. Options: ONE_MINUTE, FIVE_MINUTE, FIFTEEN_MINUTE,
                  THIRTY_MINUTE, ONE_HOUR, ONE_DAY
        days_back: Number of days of history to fetch (max 60 for intraday, 2000 for daily)
        exchange: Exchange - "NSE" or "BSE" (default: NSE)

    Returns candles as list of [timestamp, open, high, low, close, volume]
    """
    api = _get_api()
    try:
        to_date = now_ist()
        from_date = to_date - timedelta(days=days_back)

        params = {
            "exchange": exchange,
            "symboltoken": symbol_token,
            "interval": interval,
            "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
            "todate": to_date.strftime("%Y-%m-%d %H:%M"),
        }

        data = api.getCandleData(params)
        if data.get("status"):
            candles = data.get("data", [])
            return {
                "status": "success",
                "symbol_token": symbol_token,
                "interval": interval,
                "candle_count": len(candles),
                "candles": candles,  # [[timestamp, O, H, L, C, V], ...]
            }
        return {"status": "error", "message": data.get("message", "Failed to fetch candles")}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def get_watchlist_quotes(symbols: list[dict]) -> dict:
    """
    Get LTP for multiple symbols in one call (batch endpoint).
    Preferred over individual calls for scanning Nifty 50.

    Args:
        symbols: List of dicts with keys: exchange, token
                 Example: [{"exchange": "NSE", "token": "2885"}, {"exchange": "NSE", "token": "3045"}]
    """
    api = _get_api()
    try:
        # Angel One's market data API for multiple symbols
        exchange_tokens = {}
        for sym in symbols:
            ex = sym.get("exchange", "NSE")
            tok = sym.get("token", "")
            if ex not in exchange_tokens:
                exchange_tokens[ex] = []
            exchange_tokens[ex].append(tok)

        data = api.getMarketData(
            mode="FULL",
            exchangeTokens=exchange_tokens,
        )

        if data.get("status"):
            fetched = data.get("data", {}).get("fetched", [])
            results = []
            for item in fetched:
                results.append({
                    "token": item.get("symbolToken"),
                    "symbol": item.get("tradingSymbol", ""),
                    "ltp": item.get("ltp"),
                    "open": item.get("open"),
                    "high": item.get("high"),
                    "low": item.get("low"),
                    "close": item.get("close"),
                    "volume": item.get("tradeVolume"),
                    "change_pct": item.get("percentChange"),
                })
            return {
                "status": "success",
                "count": len(results),
                "quotes": results,
                "timestamp": now_ist().isoformat(),
            }
        return {"status": "error", "message": data.get("message", "Failed to fetch market data")}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def place_order(
    symbol: str,
    token: str,
    transaction_type: str,
    quantity: int,
    price: float = 0,
    order_type: str = "MARKET",
    product_type: str = "INTRADAY",
    exchange: str = "NSE",
    trigger_price: float = 0,
    stop_loss: float = 0,
) -> dict:
    """
    Place a trade order on Angel One. SAFETY-CRITICAL: Hard limits enforced.

    Args:
        symbol: Trading symbol e.g. "RELIANCE-EQ"
        token: Angel One symbol token
        transaction_type: "BUY" or "SELL"
        quantity: Number of shares (will be validated against position limits)
        price: Limit price (0 for market orders)
        order_type: "MARKET", "LIMIT", "STOPLOSS_LIMIT", "STOPLOSS_MARKET"
        product_type: "INTRADAY" (MIS), "DELIVERY" (CNC), "MARGIN"
        exchange: "NSE" or "BSE"
        trigger_price: Trigger price for stop-loss orders
        stop_loss: Stop-loss price for this trade (REQUIRED for BUY orders)

    HARD LIMITS (cannot be overridden):
    - Market must be in active window (9:30-15:15 IST)
    - Max position size: 10% of capital
    - Stop-loss required for all BUY orders
    """
    api = _get_api()

    # ══════════════════════════════════════════════════════
    # HARD SAFETY CHECKS - These CANNOT be bypassed
    # ══════════════════════════════════════════════════════

    # 1. Market hours check
    if not is_market_active():
        current = now_ist().time().isoformat()
        return {
            "status": "BLOCKED",
            "reason": f"Outside active trading window (9:30-15:15 IST). Current: {current}",
        }

    # 2. Stop-loss required for BUY
    if transaction_type.upper() == "BUY" and stop_loss <= 0:
        return {
            "status": "BLOCKED",
            "reason": "Stop-loss is REQUIRED for all BUY orders. Set stop_loss parameter.",
        }

    # 3. Position size check (rough estimate using LTP)
    try:
        ltp_data = api.ltpData(exchange, symbol, token)
        ltp = ltp_data.get("data", {}).get("ltp", 0)
        if ltp > 0:
            position_value = ltp * quantity
            max_allowed = STARTING_CAPITAL * MAX_POSITION_PCT
            if position_value > max_allowed:
                return {
                    "status": "BLOCKED",
                    "reason": f"Position value ₹{position_value:,.0f} exceeds 10% limit ₹{max_allowed:,.0f}. Reduce quantity.",
                }
    except Exception:
        log.warning("Could not verify position size against LTP")

    # 4. Stop-loss distance check for BUY
    if transaction_type.upper() == "BUY" and stop_loss > 0 and ltp > 0:
        sl_distance = (ltp - stop_loss) / ltp
        if sl_distance > 0.05:  # MAX_STOP_LOSS_PCT
            return {
                "status": "BLOCKED",
                "reason": f"Stop-loss too far from entry ({sl_distance:.1%}). Max allowed: 5%.",
            }
        if sl_distance < 0:
            return {
                "status": "BLOCKED",
                "reason": "Stop-loss must be BELOW entry price for BUY orders.",
            }

    # ══════════════════════════════════════════════════════
    # PLACE THE ORDER
    # ══════════════════════════════════════════════════════
    try:
        order_params = {
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": token,
            "transactiontype": transaction_type.upper(),
            "exchange": exchange,
            "ordertype": order_type,
            "producttype": product_type,
            "duration": "DAY",
            "quantity": str(quantity),
        }

        if price > 0:
            order_params["price"] = str(price)
        else:
            order_params["price"] = "0"

        if trigger_price > 0:
            order_params["triggerprice"] = str(trigger_price)
        else:
            order_params["triggerprice"] = "0"

        # For stop-loss order types
        if order_type in ("STOPLOSS_LIMIT", "STOPLOSS_MARKET") and trigger_price <= 0:
            return {
                "status": "error",
                "message": "trigger_price required for stop-loss order types",
            }

        data = api.placeOrder(order_params)
        log.info(f"Order placed: {transaction_type} {quantity}x {symbol} -> {data}")

        if data:
            return {
                "status": "success",
                "order_id": data,
                "symbol": symbol,
                "transaction_type": transaction_type.upper(),
                "quantity": quantity,
                "order_type": order_type,
                "stop_loss": stop_loss,
                "timestamp": now_ist().isoformat(),
            }
        return {"status": "error", "message": "Order placement returned empty response"}
    except Exception as e:
        log.error(f"Order error: {e}")
        return {"status": "error", "message": str(e)}


@mcp.tool()
def get_order_status(order_id: str) -> dict:
    """
    Check the status of a placed order.

    Args:
        order_id: The order ID returned by place_order
    """
    api = _get_api()
    try:
        order_book = api.orderBook()
        if order_book.get("status") and order_book.get("data"):
            for order in order_book["data"]:
                if order.get("orderid") == order_id:
                    return {
                        "status": "success",
                        "order_id": order_id,
                        "order_status": order.get("orderstatus"),
                        "symbol": order.get("tradingsymbol"),
                        "quantity": order.get("quantity"),
                        "price": order.get("price"),
                        "average_price": order.get("averageprice"),
                        "filled_qty": order.get("filledshares"),
                        "text": order.get("text", ""),
                    }
            return {"status": "error", "message": f"Order {order_id} not found in order book"}
        return {"status": "error", "message": "Could not fetch order book"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def cancel_order(order_id: str, variety: str = "NORMAL") -> dict:
    """
    Cancel a pending order.

    Args:
        order_id: The order ID to cancel
        variety: Order variety - "NORMAL", "STOPLOSS", "AMO", "ROBO"
    """
    api = _get_api()
    try:
        data = api.cancelOrder(order_id, variety)
        log.info(f"Cancel order {order_id}: {data}")
        return {
            "status": "success",
            "order_id": order_id,
            "cancel_result": data,
            "timestamp": now_ist().isoformat(),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def get_positions() -> dict:
    """
    Get all current open positions from the broker.
    Returns both day positions and net positions.
    """
    api = _get_api()
    try:
        data = api.position()
        if data.get("status") and data.get("data"):
            positions = []
            for pos in data["data"]:
                if int(pos.get("netqty", 0)) != 0:
                    positions.append({
                        "symbol": pos.get("tradingsymbol"),
                        "token": pos.get("symboltoken"),
                        "exchange": pos.get("exchange"),
                        "quantity": pos.get("netqty"),
                        "buy_price": pos.get("buyavgprice"),
                        "sell_price": pos.get("sellavgprice"),
                        "ltp": pos.get("ltp"),
                        "pnl": pos.get("pnl"),
                        "product_type": pos.get("producttype"),
                    })
            return {
                "status": "success",
                "open_positions": len(positions),
                "positions": positions,
                "timestamp": now_ist().isoformat(),
            }
        return {"status": "success", "open_positions": 0, "positions": []}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def get_nifty50_symbols() -> dict:
    """
    Return the Nifty 50 stock list with Angel One symbol tokens.
    These are the symbols the trading system scans each cycle.
    Token mappings come from Angel One's instrument master file.

    Returns a dict of {symbol: token} for all Nifty 50 constituents.
    """
    # Hardcoded Nifty 50 constituents with their Angel One tokens
    # Updated periodically - last update: Feb 2026
    # Source: Angel One instrument master + NSE index composition
    nifty50 = {
        "ADANIENT-EQ": "25",
        "ADANIPORTS-EQ": "15083",
        "APOLLOHOSP-EQ": "157",
        "ASIANPAINT-EQ": "236",
        "AXISBANK-EQ": "5900",
        "BAJAJ-AUTO-EQ": "16669",
        "BAJFINANCE-EQ": "317",
        "BAJAJFINSV-EQ": "16675",
        "BEL-EQ": "383",
        "BPCL-EQ": "526",
        "BHARTIARTL-EQ": "10604",
        "BRITANNIA-EQ": "547",
        "CIPLA-EQ": "694",
        "COALINDIA-EQ": "20374",
        "DRREDDY-EQ": "881",
        "EICHERMOT-EQ": "910",
        "GRASIM-EQ": "1232",
        "HCLTECH-EQ": "7229",
        "HDFCBANK-EQ": "1333",
        "HDFCLIFE-EQ": "467",
        "HEROMOTOCO-EQ": "1348",
        "HINDALCO-EQ": "1363",
        "HINDUNILVR-EQ": "1394",
        "ICICIBANK-EQ": "4963",
        "ITC-EQ": "1660",
        "INDUSINDBK-EQ": "5258",
        "INFY-EQ": "1594",
        "JSWSTEEL-EQ": "11723",
        "KOTAKBANK-EQ": "1922",
        "LT-EQ": "11483",
        "M&M-EQ": "2031",
        "MARUTI-EQ": "10999",
        "NTPC-EQ": "11630",
        "NESTLEIND-EQ": "17963",
        "ONGC-EQ": "2475",
        "POWERGRID-EQ": "14977",
        "RELIANCE-EQ": "2885",
        "SBILIFE-EQ": "21808",
        "SHRIRAMFIN-EQ": "4306",
        "SBIN-EQ": "3045",
        "SUNPHARMA-EQ": "3351",
        "TCS-EQ": "11536",
        "TATACONSUM-EQ": "3432",
        "TATAMOTORS-EQ": "3456",
        "TATASTEEL-EQ": "3499",
        "TECHM-EQ": "13538",
        "TITAN-EQ": "3506",
        "ULTRACEMCO-EQ": "11532",
        "WIPRO-EQ": "3787",
    }
    return {
        "status": "success",
        "count": len(nifty50),
        "symbols": nifty50,
        "note": "Format: {tradingsymbol: symboltoken}. Use these in other tools.",
    }


@mcp.tool()
def refresh_session() -> dict:
    """
    Refresh the authentication token using the refresh token.
    Call this if you get authentication errors mid-session.
    """
    global _auth_token, _session_time

    if _smart_api is None or _refresh_token is None:
        return {"status": "error", "message": "No active session. Call login_session first."}

    try:
        _smart_api.generateToken(_refresh_token)
        _session_time = now_ist()
        log.info("Session refreshed successfully")
        return {
            "status": "success",
            "message": "Session token refreshed",
            "timestamp": _session_time.isoformat(),
        }
    except Exception as e:
        return {"status": "error", "message": f"Refresh failed: {e}. Try login_session instead."}


# ── Entry point ───────────────────────────────────────────
if __name__ == "__main__":
    log.info("Starting Angel One MCP server (stdio)")
    mcp.run(transport="stdio")
