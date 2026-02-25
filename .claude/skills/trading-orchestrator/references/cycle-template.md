# Trading Cycle — JSON Template

---

## Cycle ID Format

- Pattern: `C{YYYYMMDD}_{sequence_number}`
- Example: `C20260222_001` (first cycle on Feb 22, 2026)
- Sequence resets daily, starts at 001
- Every cycle gets a unique ID, even if no trades are made

---

## Timestamps

- All timestamps in ISO 8601 format with IST offset: `+05:30`
- Example: `2026-02-22T10:30:00+05:30`

---

## Full Cycle JSON Template

```json
{
  "cycle_id": "C{YYYYMMDD}_{sequence_number}",
  "timestamp": "ISO 8601 with IST offset",
  "market_status": "OPEN | CLOSED | PRE_MARKET | POST_MARKET",

  "pre_check": {
    "portfolio_cash": 0.0,
    "open_positions": 0,
    "daily_pnl_pct": 0.0,
    "circuit_breaker_active": false,
    "positions_needing_attention": []
  },

  "screening": {
    "stocks_scanned": 50,
    "flagged_stocks": [
      {
        "symbol": "RELIANCE-EQ",
        "composite_score": 78,
        "classification": "BUY",
        "confidence": "HIGH",
        "key_indicators": {
          "rsi": 32.5,
          "macd_signal": "BULLISH_CROSS",
          "ema_trend": "ABOVE_ALL",
          "volume_ratio": 1.8
        }
      }
    ]
  },

  "analysis": {
    "stocks_analyzed": 1,
    "results": [
      {
        "symbol": "RELIANCE-EQ",
        "sentiment_score": 65,
        "sentiment_label": "BULLISH",
        "red_flags": [],
        "key_drivers": ["Q3 earnings beat by 12%"],
        "sector_context": "Energy sector neutral"
      }
    ]
  },

  "decisions": {
    "BUY": [
      {
        "symbol": "RELIANCE-EQ",
        "confidence": "HIGH",
        "reasoning": "Strong technicals + bullish sentiment"
      }
    ],
    "SELL": [],
    "SKIP": [],
    "HOLD": []
  },

  "execution": {
    "trades_attempted": 1,
    "trades_executed": 1,
    "trades_rejected": 0,
    "details": [
      {
        "symbol": "RELIANCE-EQ",
        "action": "BUY",
        "quantity": 4,
        "price": 2500.00,
        "stop_loss": 2425.00,
        "order_id": "ORD123456",
        "status": "EXECUTED"
      }
    ]
  },

  "monitoring": {
    "positions_checked": 3,
    "stop_loss_alerts": [],
    "trailing_stop_updates": []
  },

  "summary": {
    "total_open_positions": 4,
    "daily_pnl_pct": 0.5,
    "capital_utilization_pct": 40.0,
    "notes": "RELIANCE entry on oversold bounce + earnings beat"
  }
}
```

---

## Section-by-Section Guide

### pre_check

Populated by calling `get_portfolio_state()`, `get_daily_pnl()`, and `get_risk_metrics()`.

- `portfolio_cash`: Available cash from portfolio table
- `open_positions`: Count of positions with status='OPEN'
- `daily_pnl_pct`: Today's combined realized + unrealized P&L as percentage
- `circuit_breaker_active`: If true, STOP the cycle immediately (no screening, no trading)
- `positions_needing_attention`: Positions approaching stop-loss (within 1% of trigger)

### screening

Populated by the Screener Agent's scan of Nifty 50.

- `stocks_scanned`: Should always be 50 (full Nifty 50)
- `flagged_stocks`: Only stocks with composite_score >= 60
- If no stocks flagged, array is empty and the cycle skips analysis/execution

### analysis

Populated by the Analyst Agent for each flagged stock.

- `stocks_analyzed`: Should match the count of flagged_stocks
- Only populated if screening produced flags
- If Analyst is not activated, this section contains `"stocks_analyzed": 0, "results": []`

### decisions

Populated by the Team Lead after applying the decision matrix.

- `BUY`: Stocks approved for purchase (sent to Executor)
- `SELL`: Existing positions to close (stop-loss hit or manual exit)
- `SKIP`: Stocks that were flagged but did not pass the decision matrix
- `HOLD`: Existing positions that remain open (no action needed)

### execution

Populated by the Executor Agent after attempting trades.

- `trades_attempted`: Total BUY + SELL orders attempted
- `trades_executed`: Successfully placed and confirmed
- `trades_rejected`: Blocked by risk checks or API errors
- Each detail entry includes the order_id for Angel One tracking

### monitoring

Populated by the Executor Agent checking existing positions.

- `positions_checked`: All OPEN positions checked against current prices
- `stop_loss_alerts`: Positions where current price is within 1% of stop-loss
- `trailing_stop_updates`: If trailing stops are implemented, updates logged here

### summary

Written by the Team Lead at cycle conclusion.

- `capital_utilization_pct`: (total invested value / total capital) * 100
- `notes`: Brief human-readable summary of what happened this cycle

---

## Storage

- Store via `save_analysis()` with `analysis_type='COMBINED'` and `details_json` containing the full cycle JSON
- Alternatively, include key fields in the `reasoning` column of `log_trade()` for each trade
- Every cycle MUST be logged, even if no trades were made (for the audit trail)
- Useful for post-market review and strategy refinement

---

## Example: No-Trade Cycle

```json
{
  "cycle_id": "C20260222_003",
  "timestamp": "2026-02-22T11:00:00+05:30",
  "market_status": "OPEN",
  "pre_check": {
    "portfolio_cash": 75000.00,
    "open_positions": 3,
    "daily_pnl_pct": -0.3,
    "circuit_breaker_active": false,
    "positions_needing_attention": []
  },
  "screening": {
    "stocks_scanned": 50,
    "flagged_stocks": []
  },
  "analysis": {
    "stocks_analyzed": 0,
    "results": []
  },
  "decisions": {
    "BUY": [],
    "SELL": [],
    "SKIP": [],
    "HOLD": ["RELIANCE-EQ", "TCS-EQ", "INFY-EQ"]
  },
  "execution": {
    "trades_attempted": 0,
    "trades_executed": 0,
    "trades_rejected": 0,
    "details": []
  },
  "monitoring": {
    "positions_checked": 3,
    "stop_loss_alerts": [],
    "trailing_stop_updates": []
  },
  "summary": {
    "total_open_positions": 3,
    "daily_pnl_pct": -0.3,
    "capital_utilization_pct": 25.0,
    "notes": "No technical setups found. All existing positions healthy."
  }
}
```
