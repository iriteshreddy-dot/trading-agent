"""
Portfolio Database MCP Server
=============================
SQLite-backed portfolio management with HARD-CODED risk enforcement.
Transport: stdio (launched by Claude Code)

This is the SAFETY-CRITICAL layer. Risk limits here are in Python code,
not prompts. The LLM cannot talk its way past these checks.

Tools:
  - get_portfolio_state: Current cash, positions, daily P&L
  - get_trade_history: Past trades with filtering
  - log_trade: Record a new trade with full context
  - get_previous_analysis: Cached analysis to avoid redundant work
  - save_analysis: Cache a stock analysis
  - update_position: Update position after order fill
  - get_daily_pnl: Today's profit/loss
  - get_risk_metrics: Full risk dashboard
  - check_risk_limits: Pre-trade risk validation (SAFETY-CRITICAL)
  - initialize_portfolio: Set up fresh portfolio (run once)
"""

import json
import logging
import sqlite3
import sys
from datetime import datetime, date

from mcp.server.fastmcp import FastMCP

import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared import (
    DB_PATH,
    DAILY_LOSS_LIMIT_PCT,
    DEFAULT_STOP_LOSS_PCT,
    MAX_OPEN_POSITIONS,
    MAX_POSITION_PCT,
    MAX_STOP_LOSS_PCT,
    RISK_PER_TRADE_PCT,
    STARTING_CAPITAL,
    is_market_active,
    now_ist,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [portfolio-db-mcp] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("portfolio-db-mcp")

mcp = FastMCP("portfolio-db-mcp", json_response=True)


# ── Database Helpers ──────────────────────────────────────

def _get_db() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _dict_from_row(row: sqlite3.Row) -> dict:
    return dict(row) if row else {}


# ══════════════════════════════════════════════════════════
# TOOLS
# ══════════════════════════════════════════════════════════


@mcp.tool()
def initialize_portfolio(starting_capital: float = 100000) -> dict:
    """
    Initialize a fresh portfolio database. Run once at project start.
    Creates all tables and sets initial capital.
    WARNING: This will reset everything if tables already exist.

    Args:
        starting_capital: Starting paper trading capital in INR (default: ₹1,00,000)
    """
    import os
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = _get_db()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                cash REAL NOT NULL,
                starting_capital REAL NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS positions (
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
                UNIQUE(symbol, status) -- No duplicate open positions
            );

            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                token TEXT NOT NULL,
                transaction_type TEXT NOT NULL CHECK (transaction_type IN ('BUY', 'SELL')),
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                order_id TEXT,
                timestamp TEXT NOT NULL,
                -- Context
                technical_score REAL,
                sentiment_score REAL,
                sentiment_label TEXT,
                confidence TEXT CHECK (confidence IN ('HIGH', 'MODERATE', 'LOW')),
                reasoning TEXT,
                indicators_json TEXT,
                -- Risk
                stop_loss REAL,
                position_value REAL,
                risk_amount REAL,
                capital_at_trade REAL
            );

            CREATE TABLE IF NOT EXISTS daily_pnl (
                date TEXT PRIMARY KEY,
                realized_pnl REAL DEFAULT 0,
                unrealized_pnl REAL DEFAULT 0,
                trades_count INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                circuit_breaker_hit INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS analysis_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                analysis_type TEXT NOT NULL CHECK (analysis_type IN ('TECHNICAL', 'SENTIMENT', 'COMBINED')),
                score REAL,
                label TEXT,
                details_json TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
            CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
            CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);
            CREATE INDEX IF NOT EXISTS idx_analysis_symbol ON analysis_cache(symbol, analysis_type);
        """)

        # Initialize portfolio row if not exists
        now = now_ist().isoformat()
        conn.execute("""
            INSERT OR IGNORE INTO portfolio (id, cash, starting_capital, created_at, updated_at)
            VALUES (1, ?, ?, ?, ?)
        """, (starting_capital, starting_capital, now, now))

        # Initialize today's PnL row
        today = now_ist().date().isoformat()
        conn.execute("""
            INSERT OR IGNORE INTO daily_pnl (date) VALUES (?)
        """, (today,))

        conn.commit()
        log.info(f"Portfolio initialized with ₹{starting_capital:,.0f}")
        return {
            "status": "success",
            "message": f"Portfolio initialized with ₹{starting_capital:,.0f}",
            "db_path": DB_PATH,
        }
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


@mcp.tool()
def get_portfolio_state() -> dict:
    """
    Get current portfolio state: cash, open positions, daily P&L summary.
    This is the primary dashboard view for the trading system.
    """
    conn = _get_db()
    try:
        # Portfolio cash
        row = conn.execute("SELECT * FROM portfolio WHERE id = 1").fetchone()
        if not row:
            return {"status": "error", "message": "Portfolio not initialized. Call initialize_portfolio."}

        cash = row["cash"]
        starting = row["starting_capital"]

        # Open positions
        positions = conn.execute(
            "SELECT * FROM positions WHERE status = 'OPEN'"
        ).fetchall()
        positions_list = [_dict_from_row(p) for p in positions]

        # Calculate unrealized P&L (will need LTP from angel-one-mcp)
        total_invested = sum(p["entry_price"] * p["quantity"] for p in positions_list)

        # Today's PnL
        today = now_ist().date().isoformat()
        pnl_row = conn.execute(
            "SELECT * FROM daily_pnl WHERE date = ?", (today,)
        ).fetchone()
        daily_pnl = _dict_from_row(pnl_row) if pnl_row else {"realized_pnl": 0}

        return {
            "status": "success",
            "cash": cash,
            "starting_capital": starting,
            "total_invested": total_invested,
            "total_equity": cash + total_invested,
            "open_positions_count": len(positions_list),
            "open_positions": positions_list,
            "daily_realized_pnl": daily_pnl.get("realized_pnl", 0),
            "daily_trades": daily_pnl.get("trades_count", 0),
            "circuit_breaker_hit": bool(daily_pnl.get("circuit_breaker_hit", 0)),
            "market_active": is_market_active(),
            "timestamp": now_ist().isoformat(),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


@mcp.tool()
def check_risk_limits(
    symbol: str,
    quantity: int,
    entry_price: float,
    stop_loss: float,
    transaction_type: str = "BUY",
) -> dict:
    """
    ╔══════════════════════════════════════════════════════╗
    ║  SAFETY-CRITICAL: Pre-trade risk validation         ║
    ║  ALL checks must pass before any order is placed.   ║
    ║  These limits are in CODE, not in prompts.          ║
    ╚══════════════════════════════════════════════════════╝

    Args:
        symbol: Trading symbol e.g. "RELIANCE-EQ"
        quantity: Proposed quantity to buy
        entry_price: Expected entry price
        stop_loss: Proposed stop-loss price
        transaction_type: "BUY" or "SELL"

    Returns:
        approved: True/False
        checks: List of individual check results
        position_size: Calculated position value
        risk_amount: Amount at risk (entry - stop_loss) * quantity
    """
    checks = []
    all_passed = True

    conn = _get_db()
    try:
        portfolio = conn.execute("SELECT * FROM portfolio WHERE id = 1").fetchone()
        if not portfolio:
            return {"approved": False, "reason": "Portfolio not initialized"}

        cash = portfolio["cash"]
        capital = portfolio["starting_capital"]

        # ── CHECK 1: Market active ────────────────────
        market_ok = is_market_active()
        checks.append({
            "check": "market_active",
            "passed": market_ok,
            "detail": "9:30-15:15 IST" if market_ok else f"Outside window. Current: {now_ist().time().isoformat()}",
        })
        if not market_ok:
            all_passed = False

        # ── CHECK 2: Daily loss limit ─────────────────
        today = now_ist().date().isoformat()
        pnl_row = conn.execute(
            "SELECT * FROM daily_pnl WHERE date = ?", (today,)
        ).fetchone()
        daily_loss = abs(min(0, pnl_row["realized_pnl"])) if pnl_row else 0
        loss_limit = capital * DAILY_LOSS_LIMIT_PCT
        loss_ok = daily_loss < loss_limit
        checks.append({
            "check": "daily_loss_limit",
            "passed": loss_ok,
            "detail": f"Daily loss ₹{daily_loss:,.0f} / limit ₹{loss_limit:,.0f} ({DAILY_LOSS_LIMIT_PCT:.0%})",
        })
        if not loss_ok:
            all_passed = False

        # ── CHECK 3: Circuit breaker not hit ──────────
        cb_hit = bool(pnl_row["circuit_breaker_hit"]) if pnl_row else False
        checks.append({
            "check": "circuit_breaker",
            "passed": not cb_hit,
            "detail": "CIRCUIT BREAKER HIT - All trading halted today" if cb_hit else "OK",
        })
        if cb_hit:
            all_passed = False

        # ── CHECK 4: Open positions < max ─────────────
        open_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM positions WHERE status = 'OPEN'"
        ).fetchone()["cnt"]
        positions_ok = open_count < MAX_OPEN_POSITIONS
        checks.append({
            "check": "open_positions",
            "passed": positions_ok,
            "detail": f"{open_count} / {MAX_OPEN_POSITIONS} max",
        })
        if not positions_ok and transaction_type.upper() == "BUY":
            all_passed = False

        # ── CHECK 5: Not already holding this stock ───
        existing = conn.execute(
            "SELECT * FROM positions WHERE symbol = ? AND status = 'OPEN'",
            (symbol,),
        ).fetchone()
        no_duplicate = existing is None
        checks.append({
            "check": "no_duplicate_position",
            "passed": no_duplicate,
            "detail": f"Already holding {existing['quantity']} shares" if existing else "No existing position",
        })
        if not no_duplicate and transaction_type.upper() == "BUY":
            all_passed = False

        # ── CHECK 6: Position size within 10% ─────────
        position_value = entry_price * quantity
        max_position = capital * MAX_POSITION_PCT
        size_ok = position_value <= max_position
        checks.append({
            "check": "position_size",
            "passed": size_ok,
            "detail": f"₹{position_value:,.0f} / max ₹{max_position:,.0f} ({MAX_POSITION_PCT:.0%} of capital)",
        })
        if not size_ok:
            all_passed = False

        # ── CHECK 7: Stop-loss set and valid ──────────
        sl_set = stop_loss > 0
        sl_distance = (entry_price - stop_loss) / entry_price if entry_price > 0 and stop_loss > 0 else 0
        sl_ok = sl_set and DEFAULT_STOP_LOSS_PCT * 0.5 <= sl_distance <= MAX_STOP_LOSS_PCT
        checks.append({
            "check": "stop_loss_valid",
            "passed": sl_ok,
            "detail": f"SL at ₹{stop_loss:,.1f} ({sl_distance:.1%} from entry). Required: {DEFAULT_STOP_LOSS_PCT:.0%}-{MAX_STOP_LOSS_PCT:.0%}",
        })
        if not sl_ok and transaction_type.upper() == "BUY":
            all_passed = False

        # ── CHECK 8: Sufficient cash ──────────────────
        cash_ok = cash >= position_value
        checks.append({
            "check": "sufficient_cash",
            "passed": cash_ok,
            "detail": f"Cash ₹{cash:,.0f} / needed ₹{position_value:,.0f}",
        })
        if not cash_ok and transaction_type.upper() == "BUY":
            all_passed = False

        # ── Risk calculation ──────────────────────────
        risk_amount = (entry_price - stop_loss) * quantity if stop_loss > 0 else 0
        max_risk = capital * RISK_PER_TRADE_PCT

        return {
            "approved": all_passed,
            "checks": checks,
            "checks_passed": sum(1 for c in checks if c["passed"]),
            "checks_total": len(checks),
            "position_value": position_value,
            "risk_amount": risk_amount,
            "max_risk_per_trade": max_risk,
            "recommended_quantity": int(max_risk / (entry_price - stop_loss)) if stop_loss > 0 and entry_price > stop_loss else 0,
        }
    except Exception as e:
        return {"approved": False, "reason": str(e)}
    finally:
        conn.close()


@mcp.tool()
def log_trade(
    symbol: str,
    token: str,
    transaction_type: str,
    quantity: int,
    price: float,
    order_id: str = "",
    technical_score: float = 0,
    sentiment_score: float = 0,
    sentiment_label: str = "",
    confidence: str = "LOW",
    reasoning: str = "",
    indicators_json: str = "",
    stop_loss: float = 0,
) -> dict:
    """
    Record a trade in the journal with full context and reasoning.
    Every trade MUST be logged, including the reasoning behind it.

    Args:
        symbol: Trading symbol
        token: Angel One token
        transaction_type: "BUY" or "SELL"
        quantity: Number of shares
        price: Execution price
        order_id: Broker order ID
        technical_score: Score from technical analysis (0-100)
        sentiment_score: Score from sentiment analysis (-100 to 100)
        sentiment_label: "BULLISH", "BEARISH", or "NEUTRAL"
        confidence: "HIGH", "MODERATE", or "LOW"
        reasoning: Free-text reasoning for this trade
        indicators_json: JSON string of indicator values at time of trade
        stop_loss: Stop-loss price set for this trade
    """
    conn = _get_db()
    try:
        now = now_ist()
        trade_id = f"T{now.strftime('%Y%m%d%H%M%S')}_{symbol.replace('-', '')}"

        portfolio = conn.execute("SELECT * FROM portfolio WHERE id = 1").fetchone()
        capital_at_trade = portfolio["cash"] if portfolio else 0
        position_value = price * quantity
        risk_amount = (price - stop_loss) * quantity if stop_loss > 0 else 0

        conn.execute("""
            INSERT INTO trades (
                trade_id, symbol, token, transaction_type, quantity, price,
                order_id, timestamp, technical_score, sentiment_score,
                sentiment_label, confidence, reasoning, indicators_json,
                stop_loss, position_value, risk_amount, capital_at_trade
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_id, symbol, token, transaction_type.upper(), quantity, price,
            order_id, now.isoformat(), technical_score, sentiment_score,
            sentiment_label, confidence, reasoning, indicators_json,
            stop_loss, position_value, risk_amount, capital_at_trade,
        ))

        # Update daily PnL counter
        today = now.date().isoformat()
        conn.execute("""
            INSERT INTO daily_pnl (date, trades_count)
            VALUES (?, 1)
            ON CONFLICT(date) DO UPDATE SET trades_count = trades_count + 1
        """, (today,))

        conn.commit()
        log.info(f"Trade logged: {trade_id} - {transaction_type} {quantity}x {symbol} @ ₹{price}")
        return {
            "status": "success",
            "trade_id": trade_id,
            "symbol": symbol,
            "transaction_type": transaction_type.upper(),
            "position_value": position_value,
            "risk_amount": risk_amount,
        }
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


@mcp.tool()
def update_position(
    symbol: str,
    action: str,
    quantity: int = 0,
    entry_price: float = 0,
    stop_loss: float = 0,
    exit_price: float = 0,
    token: str = "",
    trade_id: str = "",
) -> dict:
    """
    Open or close a position in the portfolio tracker.

    Args:
        symbol: Trading symbol
        action: "OPEN" to create position, "CLOSE" to close existing
        quantity: Number of shares (for OPEN)
        entry_price: Entry price (for OPEN)
        stop_loss: Stop-loss price (for OPEN)
        exit_price: Exit price (for CLOSE)
        token: Angel One token (for OPEN)
        trade_id: Associated trade ID
    """
    conn = _get_db()
    try:
        now = now_ist()

        if action.upper() == "OPEN":
            # Deduct cash
            position_value = entry_price * quantity
            conn.execute(
                "UPDATE portfolio SET cash = cash - ?, updated_at = ? WHERE id = 1",
                (position_value, now.isoformat()),
            )

            conn.execute("""
                INSERT INTO positions (symbol, token, quantity, entry_price, stop_loss, entry_time, trade_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN')
            """, (symbol, token, quantity, entry_price, stop_loss, now.isoformat(), trade_id))

            conn.commit()
            return {
                "status": "success",
                "action": "OPENED",
                "symbol": symbol,
                "quantity": quantity,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "position_value": position_value,
            }

        elif action.upper() == "CLOSE":
            pos = conn.execute(
                "SELECT * FROM positions WHERE symbol = ? AND status = 'OPEN'",
                (symbol,),
            ).fetchone()

            if not pos:
                return {"status": "error", "message": f"No open position found for {symbol}"}

            pnl = (exit_price - pos["entry_price"]) * pos["quantity"]
            position_value = exit_price * pos["quantity"]

            # Return cash + PnL
            conn.execute(
                "UPDATE portfolio SET cash = cash + ?, updated_at = ? WHERE id = 1",
                (position_value, now.isoformat()),
            )

            # Close position
            conn.execute("""
                UPDATE positions SET
                    status = 'CLOSED', exit_price = ?, exit_time = ?, pnl = ?
                WHERE id = ?
            """, (exit_price, now.isoformat(), pnl, pos["id"]))

            # Update daily PnL
            today = now.date().isoformat()
            win_inc = 1 if pnl > 0 else 0
            loss_inc = 1 if pnl < 0 else 0
            conn.execute("""
                INSERT INTO daily_pnl (date, realized_pnl, wins, losses)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    realized_pnl = realized_pnl + ?,
                    wins = wins + ?,
                    losses = losses + ?
            """, (today, pnl, win_inc, loss_inc, pnl, win_inc, loss_inc))

            # Check circuit breaker
            pnl_row = conn.execute(
                "SELECT realized_pnl FROM daily_pnl WHERE date = ?", (today,)
            ).fetchone()
            total_daily_loss = abs(min(0, pnl_row["realized_pnl"]))
            loss_limit = STARTING_CAPITAL * DAILY_LOSS_LIMIT_PCT

            if total_daily_loss >= loss_limit:
                conn.execute(
                    "UPDATE daily_pnl SET circuit_breaker_hit = 1 WHERE date = ?",
                    (today,),
                )
                log.warning(f"🚨 CIRCUIT BREAKER HIT! Daily loss ₹{total_daily_loss:,.0f} >= limit ₹{loss_limit:,.0f}")

            conn.commit()
            return {
                "status": "success",
                "action": "CLOSED",
                "symbol": symbol,
                "quantity": pos["quantity"],
                "entry_price": pos["entry_price"],
                "exit_price": exit_price,
                "pnl": pnl,
                "circuit_breaker_hit": total_daily_loss >= loss_limit,
            }
        else:
            return {"status": "error", "message": f"Invalid action: {action}. Use OPEN or CLOSE."}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


@mcp.tool()
def get_daily_pnl(date_str: str = "") -> dict:
    """
    Get profit/loss summary for a specific date.

    Args:
        date_str: Date in YYYY-MM-DD format (default: today)
    """
    conn = _get_db()
    try:
        if not date_str:
            date_str = now_ist().date().isoformat()

        row = conn.execute(
            "SELECT * FROM daily_pnl WHERE date = ?", (date_str,)
        ).fetchone()

        if row:
            result = _dict_from_row(row)
            result["capital"] = STARTING_CAPITAL
            result["loss_limit"] = STARTING_CAPITAL * DAILY_LOSS_LIMIT_PCT
            result["loss_limit_remaining"] = max(0, result["loss_limit"] - abs(min(0, result["realized_pnl"])))
            return {"status": "success", **result}
        return {"status": "success", "date": date_str, "realized_pnl": 0, "trades_count": 0}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


@mcp.tool()
def get_risk_metrics() -> dict:
    """
    Full risk dashboard: current exposure, win rate, drawdown, position distribution.
    Call this for the Lead agent's pre-cycle health check.
    """
    conn = _get_db()
    try:
        portfolio = conn.execute("SELECT * FROM portfolio WHERE id = 1").fetchone()
        if not portfolio:
            return {"status": "error", "message": "Portfolio not initialized"}

        cash = portfolio["cash"]
        capital = portfolio["starting_capital"]

        # Open positions
        positions = conn.execute("SELECT * FROM positions WHERE status = 'OPEN'").fetchall()
        total_invested = sum(p["entry_price"] * p["quantity"] for p in positions)
        total_at_risk = sum((p["entry_price"] - p["stop_loss"]) * p["quantity"] for p in positions)

        # Historical stats
        closed = conn.execute("SELECT pnl FROM positions WHERE status = 'CLOSED'").fetchall()
        wins = sum(1 for t in closed if t["pnl"] and t["pnl"] > 0)
        losses = sum(1 for t in closed if t["pnl"] and t["pnl"] < 0)
        total_trades = len(closed)
        win_rate = wins / total_trades if total_trades > 0 else 0

        total_profit = sum(t["pnl"] for t in closed if t["pnl"] and t["pnl"] > 0)
        total_loss = abs(sum(t["pnl"] for t in closed if t["pnl"] and t["pnl"] < 0))
        profit_factor = total_profit / total_loss if total_loss > 0 else float("inf")

        # Today
        today = now_ist().date().isoformat()
        pnl_today = conn.execute("SELECT * FROM daily_pnl WHERE date = ?", (today,)).fetchone()

        return {
            "status": "success",
            "capital": capital,
            "cash": cash,
            "total_invested": total_invested,
            "equity": cash + total_invested,
            "return_pct": ((cash + total_invested) - capital) / capital,
            "open_positions": len(positions),
            "max_positions": MAX_OPEN_POSITIONS,
            "total_at_risk": total_at_risk,
            "exposure_pct": total_invested / capital if capital > 0 else 0,
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "today_pnl": pnl_today["realized_pnl"] if pnl_today else 0,
            "today_trades": pnl_today["trades_count"] if pnl_today else 0,
            "circuit_breaker_hit": bool(pnl_today["circuit_breaker_hit"]) if pnl_today else False,
            "daily_loss_limit": capital * DAILY_LOSS_LIMIT_PCT,
            "timestamp": now_ist().isoformat(),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


@mcp.tool()
def get_trade_history(
    symbol: str = "",
    limit: int = 20,
    transaction_type: str = "",
) -> dict:
    """
    Get past trades from the journal.

    Args:
        symbol: Filter by symbol (empty for all)
        limit: Max number of trades to return
        transaction_type: Filter by "BUY" or "SELL" (empty for all)
    """
    conn = _get_db()
    try:
        query = "SELECT * FROM trades WHERE 1=1"
        params = []

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        if transaction_type:
            query += " AND transaction_type = ?"
            params.append(transaction_type.upper())

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        trades = [_dict_from_row(r) for r in rows]
        return {"status": "success", "count": len(trades), "trades": trades}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


@mcp.tool()
def save_analysis(
    symbol: str,
    analysis_type: str,
    score: float,
    label: str = "",
    details_json: str = "",
    ttl_minutes: int = 30,
) -> dict:
    """
    Cache a stock analysis to avoid redundant computation.

    Args:
        symbol: Stock symbol
        analysis_type: "TECHNICAL", "SENTIMENT", or "COMBINED"
        score: Numeric score
        label: Text label (e.g., "BULLISH", "OVERSOLD")
        details_json: JSON string with full analysis details
        ttl_minutes: How long this analysis stays valid (default: 30 min)
    """
    conn = _get_db()
    try:
        now = now_ist()
        expires = now + __import__("datetime").timedelta(minutes=ttl_minutes)

        conn.execute("""
            INSERT INTO analysis_cache (symbol, analysis_type, score, label, details_json, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (symbol, analysis_type.upper(), score, label, details_json, now.isoformat(), expires.isoformat()))

        conn.commit()
        return {"status": "success", "symbol": symbol, "type": analysis_type, "expires_at": expires.isoformat()}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


@mcp.tool()
def get_previous_analysis(
    symbol: str,
    analysis_type: str = "",
) -> dict:
    """
    Get cached analysis for a symbol (only non-expired).

    Args:
        symbol: Stock symbol
        analysis_type: "TECHNICAL", "SENTIMENT", "COMBINED" (empty for all)
    """
    conn = _get_db()
    try:
        now = now_ist().isoformat()
        query = "SELECT * FROM analysis_cache WHERE symbol = ? AND expires_at > ?"
        params = [symbol, now]

        if analysis_type:
            query += " AND analysis_type = ?"
            params.append(analysis_type.upper())

        query += " ORDER BY created_at DESC LIMIT 5"
        rows = conn.execute(query, params).fetchall()
        analyses = [_dict_from_row(r) for r in rows]
        return {"status": "success", "count": len(analyses), "analyses": analyses}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()


# ── Entry point ───────────────────────────────────────────
if __name__ == "__main__":
    log.info("Starting Portfolio DB MCP server (stdio)")
    mcp.run(transport="stdio")
