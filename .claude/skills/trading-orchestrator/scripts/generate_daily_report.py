"""
Generate end-of-day trading report.
Called at 3:30 PM IST after market close.

Summarizes: trades, P&L, win rate, risk metrics, capital utilization.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def generate_daily_report(
    portfolio_state: dict,
    daily_pnl: dict,
    risk_metrics: dict,
    trade_history: list[dict],
) -> str:
    """
    Generate a formatted daily trading report.

    Args:
        portfolio_state: From get_portfolio_state() MCP tool
        daily_pnl: From get_daily_pnl() MCP tool
        risk_metrics: From get_risk_metrics() MCP tool
        trade_history: From get_trade_history() MCP tool (today only)

    Returns:
        Formatted markdown report string
    """
    today = datetime.now(IST).strftime("%Y-%m-%d")

    # Extract metrics
    cash = portfolio_state.get("cash", 0)
    capital = portfolio_state.get("starting_capital", 100000)
    open_positions = portfolio_state.get("open_positions_count", 0)

    realized_pnl = daily_pnl.get("realized_pnl", 0)
    trades_count = daily_pnl.get("trades_count", 0)
    wins = daily_pnl.get("wins", 0)
    losses = daily_pnl.get("losses", 0)
    circuit_breaker = daily_pnl.get("circuit_breaker_hit", False)

    win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
    total_invested = risk_metrics.get("total_invested", 0)
    utilization = (total_invested / capital * 100) if capital > 0 else 0

    report = f"""# Daily Trading Report — {today}

## Summary
- **Realized P&L:** ₹{realized_pnl:,.2f} ({realized_pnl/capital*100:.2f}%)
- **Trades Today:** {trades_count}
- **Win Rate:** {win_rate:.0f}% ({wins}W / {losses}L)
- **Circuit Breaker:** {'TRIGGERED' if circuit_breaker else 'Not hit'}

## Portfolio State
- **Cash Available:** ₹{cash:,.2f}
- **Open Positions:** {open_positions}
- **Capital Utilization:** {utilization:.1f}%
- **Total Equity:** ₹{risk_metrics.get('equity', capital):,.2f}

## Risk Metrics
- **Daily Loss Limit Remaining:** ₹{risk_metrics.get('daily_loss_limit', 2000) - abs(min(realized_pnl, 0)):,.2f}
- **Max Single Loss Today:** ₹{min([t.get('pnl', 0) for t in trade_history] or [0]):,.2f}
- **Exposure:** {risk_metrics.get('exposure_pct', 0):.1f}%

## Trades
"""
    if trade_history:
        for trade in trade_history:
            report += f"- {trade.get('transaction_type', '?')} {trade.get('symbol', '?')}: "
            report += f"{trade.get('quantity', 0)} @ ₹{trade.get('price', 0):,.2f}"
            if trade.get('pnl') is not None:
                report += f" (P&L: ₹{trade['pnl']:,.2f})"
            report += f" [{trade.get('confidence', 'N/A')}]\n"
    else:
        report += "- No trades executed today\n"

    report += f"""
## Notes
- Review flagged stocks that were skipped for potential next-day opportunities
- Check if any open positions need stop-loss adjustment
- Generated at {datetime.now(IST).strftime('%H:%M IST')}
"""
    return report


if __name__ == "__main__":
    # Example with dummy data
    report = generate_daily_report(
        portfolio_state={"cash": 90000, "starting_capital": 100000, "open_positions_count": 2},
        daily_pnl={"realized_pnl": 500, "trades_count": 3, "wins": 2, "losses": 1, "circuit_breaker_hit": False},
        risk_metrics={"total_invested": 20000, "equity": 100500, "exposure_pct": 20, "daily_loss_limit": 2000},
        trade_history=[
            {"transaction_type": "BUY", "symbol": "RELIANCE-EQ", "quantity": 4, "price": 2500, "confidence": "HIGH"},
            {"transaction_type": "SELL", "symbol": "TCS-EQ", "quantity": 3, "price": 3800, "pnl": 300, "confidence": "MODERATE"},
        ],
    )
    print(report)
