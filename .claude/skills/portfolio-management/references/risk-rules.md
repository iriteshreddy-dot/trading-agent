# Risk Rules — Detailed Reference

All 6 immutable risk rules are enforced in MCP server code and cannot be overridden by agents.

---

## Rule 1: Position Size Limit (10%)

- **Rule**: Max position value = `current_capital * 0.10`
- **Based on**: CURRENT capital (not starting capital), so it adjusts as P&L changes
- **Edge case**: If capital drops to Rs.80,000, max position is Rs.8,000 (not Rs.10,000)
- **Edge case**: If capital grows to Rs.1,20,000, max position is Rs.12,000
- **Enforced in**: `angel-one-mcp` `place_order()` AND `portfolio-db-mcp` `check_risk_limits()`
- **Double enforcement**: Both servers validate independently; either can reject

---

## Rule 2: Maximum 5 Open Positions

- **Rule**: Hard limit on concurrent OPEN positions
- **Counted via**: `COUNT(*)` query on `positions` table `WHERE status='OPEN'`
- **Edge case**: If 5 positions open and one hits stop-loss, can open a new one AFTER the CLOSE is logged via `update_position()`
- **Edge case**: A position is only "closed" when `update_position()` sets `status='CLOSED'` -- simply placing a SELL order does not free the slot
- **Enforced in**: `portfolio-db-mcp` `check_risk_limits()`

---

## Rule 3: Daily Loss Limit 2% (Circuit Breaker)

- **Rule**: If `realized_pnl + unrealized_pnl` loss exceeds 2% of capital, ALL trading halts
- **Starting capital** Rs.1,00,000 -> limit is Rs.2,000 loss
- **Edge case**: Circuit breaker stays active for the rest of the trading day. Resets the next trading day.
- **Edge case**: Existing positions remain open (do NOT panic-sell). Only new BUY orders are blocked.
- **Edge case**: SELL orders for existing positions are still allowed (to close positions)
- **Tracked in**: `daily_pnl` table, `circuit_breaker_hit` column
- **Enforced in**: `portfolio-db-mcp` `check_risk_limits()` and `update_position()`

---

## Rule 4: Mandatory Stop-Loss (3-5%)

- **Rule**: Every BUY order MUST include a `stop_loss` value greater than 0
- **Distance**: 3% below entry (default) to 5% below entry (maximum allowed)
- **Can be tightened**: A stop-loss of 2% below entry is acceptable (tighter = less risk)
- **Cannot be widened**: A stop-loss beyond 5% below entry is REJECTED
- **Edge case**: Stop-loss of exactly 5% is accepted; 5.01% is rejected
- **Edge case**: Stop-loss at 0 or negative values are rejected
- **Enforced in**: `angel-one-mcp` `place_order()` validates the distance calculation

---

## Rule 5: Trading Window (9:30 AM - 3:15 PM IST)

- **Rule**: No orders accepted outside the trading window
- **Window**: 09:30:00 IST to 15:15:00 IST
- **Edge case**: Order at 15:14:59 goes through. Order at 15:15:01 is rejected.
- **Edge case**: Market opens at 9:15 IST but we intentionally skip the first 15 minutes to avoid opening volatility
- **Edge case**: Pre-market (9:00-9:15) and post-market (15:30-16:00) sessions are NOT used
- **Enforced in**: `angel-one-mcp` `place_order()` and `portfolio-db-mcp` `check_risk_limits()`

---

## Rule 6: No Duplicate Positions

- **Rule**: Cannot hold more than 1 OPEN position in the same stock symbol
- **Enforced via**: `UNIQUE(symbol, status)` constraint in the `positions` table
- **Edge case**: CAN buy RELIANCE after closing a previous RELIANCE position (old row has `status='CLOSED'`, new row has `status='OPEN'` -- unique constraint satisfied)
- **Edge case**: Attempting to BUY a stock already held as OPEN will result in a database constraint violation
- **Edge case**: Different exchange variants of the same stock (e.g., NSE vs BSE) are treated as the same if the symbol matches

---

## Enforcement Summary

| Rule | angel-one-mcp | portfolio-db-mcp |
|------|:---:|:---:|
| 10% position limit | Yes | Yes |
| Max 5 positions | No | Yes |
| 2% daily loss limit | No | Yes |
| Mandatory stop-loss | Yes | No |
| Trading window | Yes | Yes |
| No duplicates | No | Yes (DB constraint) |
