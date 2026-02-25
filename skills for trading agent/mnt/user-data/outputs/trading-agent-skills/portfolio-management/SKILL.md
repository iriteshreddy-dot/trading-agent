---
name: portfolio-management
description: Manage trading portfolio, enforce risk rules, calculate position sizes, and maintain trade journals. Use this skill BEFORE executing any trade to validate risk limits, calculate correct position size, and set stop-losses. Also use for portfolio reviews, P&L tracking, and generating trade reports. Trigger whenever trades are being considered, positions need managing, risk needs checking, or portfolio state is needed. THIS SKILL CONTAINS IMMUTABLE RISK RULES THAT CANNOT BE OVERRIDDEN.
---

# Portfolio Management Skill — Risk & Execution

## Overview

This is the **safety-critical skill**. It enforces risk management rules that protect capital. Every trade MUST pass through this skill's validation before execution.

## IMMUTABLE RISK RULES

**These rules are hard-coded in the MCP server. Even if the LLM is "convinced" to bypass them, the MCP server will reject the trade.**

### Rule 1: Position Size Limit
- Max 10% of CURRENT capital per stock
- Calculation: `max_position = current_capital * 0.10`
- This is based on current capital, not starting capital

### Rule 2: Maximum Open Positions
- Max 5 simultaneous positions
- If 5 positions are open, NO new BUY orders until one is closed

### Rule 3: Daily Loss Limit
- If daily realized + unrealized loss exceeds 2% of capital → STOP ALL TRADING
- This is a circuit breaker. No new trades for the rest of the day.
- Existing positions remain (don't panic-sell), but no new entries.

### Rule 4: Mandatory Stop-Loss
- Every position MUST have a stop-loss set at entry time
- Default: 3% below entry price
- Can be tightened (closer to entry) but NEVER widened beyond 5%

### Rule 5: Trading Window
- No new trades in first 15 minutes (9:15-9:30 IST) — let opening volatility settle
- No new trades in last 15 minutes (3:15-3:30 IST) — avoid closing auction effects
- Active window: 9:30 AM - 3:15 PM IST

### Rule 6: Single Stock Concentration
- Never hold more than 1 position in the same stock
- If already holding RELIANCE, cannot buy more RELIANCE

## Position Sizing

Run `scripts/calculate_position_size.py` for exact calculations.

### Fixed Fractional Method (Default)
```
risk_per_trade = current_capital * 0.01  (1% risk per trade)
position_size = risk_per_trade / (entry_price - stop_loss_price)
quantity = min(position_size, max_position_limit / entry_price)
quantity = floor(quantity)  # Always round DOWN, never up
```

### Example:
```
Capital: ₹1,00,000
Stock: RELIANCE at ₹2,500
Stop-loss: ₹2,425 (3% below entry)

risk_per_trade = 1,00,000 * 0.01 = ₹1,000
position_size = 1,000 / (2,500 - 2,425) = 1,000 / 75 = 13.3
quantity = floor(13.3) = 13 shares

Max position check: 13 * 2,500 = ₹32,500 (32.5% > 10% limit!)
Adjusted: floor(10,000 / 2,500) = 4 shares
Final quantity: 4 shares = ₹10,000 (10% of capital) ✓
```

## Pre-Trade Validation Checklist

Before executing ANY trade, validate ALL of the following:

```
scripts/check_risk_limits.py runs this checklist:

□ Market is in active trading window?
□ Daily loss limit not hit?
□ Number of open positions < 5?
□ Not already holding this stock?
□ Position size within 10% limit?
□ Stop-loss is set and within 3-5% range?
□ Sufficient cash balance for the trade?
□ Technical signal score ≥ 60?
□ No sentiment red flags (veto active)?
```

**ALL checks must pass. If ANY fails, the trade is REJECTED.**

## Trade Journaling

Every trade (entry and exit) MUST be logged via `portfolio-db-mcp`:

```json
{
  "trade_id": "T20260222_001",
  "timestamp": "2026-02-22T10:35:00+05:30",
  "symbol": "NSE:RELIANCE",
  "action": "BUY",
  "quantity": 4,
  "price": 2500.00,
  "stop_loss": 2425.00,
  "target": 2650.00,
  "reasoning": {
    "technical_score": 72,
    "sentiment": "BULLISH",
    "key_factors": [
      "RSI at 33 (oversold)",
      "Price at 50-EMA support",
      "Q3 earnings beat by 12%"
    ],
    "confidence": "MODERATE"
  },
  "risk_metrics": {
    "position_pct_of_capital": 10.0,
    "risk_amount": 300,
    "risk_reward_ratio": 2.0,
    "open_positions_after": 3
  }
}
```

## Position Monitoring

During each cycle, check all open positions:

1. **Stop-loss hit?** → Execute market SELL immediately, log exit
2. **Target reached?** → Execute limit SELL, log exit
3. **Trailing stop update?** → If price moved >2% in favor, trail stop to breakeven
4. **Time-based exit?** → If holding >5 days with no target hit, review and decide

## Daily Report

At market close (3:30 PM), generate via `scripts/generate_daily_report.py`:
- Total trades today (entries + exits)
- Realized P&L for the day
- Unrealized P&L on open positions
- Win rate (winning trades / total exits)
- Average risk-reward achieved
- Capital utilization percentage
- Largest single loss
- Notes on what worked and what didn't

## Reference Files

- `references/risk-rules.md` — Detailed explanation of each rule with edge cases
- `references/portfolio-schema.md` — SQLite table definitions
- `references/trade-journal-format.md` — Complete journaling specification
