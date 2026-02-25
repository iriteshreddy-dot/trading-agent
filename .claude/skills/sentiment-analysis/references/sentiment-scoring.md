# Sentiment Scoring Rubric

**Score Scale: -100 to +100**

**Scoring by News Type:**

| News Category | Bullish Score | Bearish Score | Examples |
|---|---|---|---|
| Earnings beat (>10%) | +40 to +60 | — | "Q3 profit up 25% YoY" |
| Earnings miss (>10%) | — | -40 to -60 | "Revenue misses estimates by 15%" |
| Analyst upgrade | +20 to +30 | — | "Morgan Stanley upgrades to Overweight" |
| Analyst downgrade | — | -20 to -30 | "Goldman cuts target price by 20%" |
| Management guidance up | +30 to +50 | — | "Company raises FY27 guidance" |
| Management guidance cut | — | -30 to -50 | "Revenue guidance lowered" |
| Dividend/buyback announced | +10 to +20 | — | "Board approves ₹10 special dividend" |
| SEBI investigation | — | -50 to -80 | "SEBI issues show-cause notice" |
| Auditor resignation | — | -60 to -80 | "Statutory auditor resigns" |
| Promoter pledge >50% | — | -40 to -60 | "Promoter pledges 55% of holdings" |
| New partnership/contract | +15 to +30 | — | "Wins ₹5000 Cr government contract" |
| Debt downgrade | — | -30 to -50 | "Moody's downgrades to Ba1" |
| FII buying >₹2000 Cr | +15 to +25 | — | (market-level, applies to all stocks) |
| FII selling >₹2000 Cr | — | -15 to -25 | (market-level) |

**Time Decay Multipliers:**
- < 1 hour: 1.0x
- 1-6 hours: 0.8x
- 6-24 hours: 0.5x
- 1-3 days: 0.2x
- > 3 days: 0.0x (ignore, except structural news)

**Aggregation:**
- Multiple news items: weighted average by recency and source reliability
- If conflicting signals: take the more negative view (safety bias)
- Red flags always override to BEARISH regardless of other positive news
