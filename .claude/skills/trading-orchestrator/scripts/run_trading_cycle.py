"""
Trading cycle orchestration template.
Defines the 7-phase cycle that the Team Lead follows.

This is a reference implementation. The actual orchestration happens
through Claude Code agent teams with the trading-orchestrator skill.
"""

import json
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def create_cycle_id() -> str:
    """Generate a unique cycle ID: C{YYYYMMDD}_{sequence}"""
    now = datetime.now(IST)
    return f"C{now.strftime('%Y%m%d')}_{now.strftime('%H%M%S')}"


def create_cycle_log(
    cycle_id: str,
    pre_check: dict,
    screening: dict,
    analysis: dict,
    decisions: dict,
    execution: dict,
    monitoring: dict,
    notes: str = "",
) -> dict:
    """
    Create a structured cycle log entry.

    This is the template the Lead agent should follow when summarizing each cycle.
    """
    now = datetime.now(IST)

    return {
        "cycle_id": cycle_id,
        "timestamp": now.isoformat(),
        "pre_check": pre_check,
        "screening": {
            "stocks_scanned": screening.get("stocks_scanned", 50),
            "flagged_stocks": screening.get("flagged_stocks", []),
        },
        "analysis": {
            "stocks_analyzed": analysis.get("stocks_analyzed", 0),
            "results": analysis.get("results", []),
        },
        "decisions": {
            "BUY": decisions.get("BUY", []),
            "SELL": decisions.get("SELL", []),
            "SKIP": decisions.get("SKIP", []),
            "HOLD": decisions.get("HOLD", []),
        },
        "execution": {
            "trades_attempted": execution.get("trades_attempted", 0),
            "trades_executed": execution.get("trades_executed", 0),
            "trades_rejected": execution.get("trades_rejected", 0),
            "details": execution.get("details", []),
        },
        "monitoring": {
            "positions_checked": monitoring.get("positions_checked", 0),
            "stop_loss_alerts": monitoring.get("stop_loss_alerts", []),
            "trailing_stop_updates": monitoring.get("trailing_stop_updates", []),
        },
        "summary": {
            "notes": notes,
        },
    }


CYCLE_PHASES = """
Trading Cycle — 7 Phases
=========================

Phase 1: PRE-CHECK (Lead)
  - get_portfolio_state() → cash, positions, daily P&L
  - get_daily_pnl() → circuit breaker status
  - get_risk_metrics() → full dashboard
  - IF circuit breaker hit → STOP

Phase 2: SCREENING (Screener Agent)
  - get_nifty50_symbols() → all 50 stocks
  - get_watchlist_quotes() → batch current prices
  - Compute RSI, MACD, EMA for each
  - Flag stocks with composite score ≥ 60

Phase 3: ANALYSIS (Analyst Agent)
  - Only if ≥1 stock flagged
  - get_stock_news() → recent headlines
  - get_fii_dii_data() → institutional flows
  - Score sentiment, detect red flags

Phase 4: DECISION (Lead)
  - Apply decision matrix (4 criteria)
  - ALL pass → EXECUTE
  - 3 of 4 → CAUTION (75% size)
  - ≤2 → SKIP

Phase 5: EXECUTION (Executor Agent)
  - check_risk_limits() FIRST
  - If approved: place_order() → log_trade() → update_position()
  - If rejected: log reason, skip

Phase 6: MONITORING (Executor Agent)
  - Check all open positions
  - Stop-loss proximity alerts
  - Trailing stop updates

Phase 7: SUMMARY (Lead)
  - Log complete cycle
  - Note decisions and reasoning
"""


if __name__ == "__main__":
    print(CYCLE_PHASES)
    print(f"\nExample cycle ID: {create_cycle_id()}")
