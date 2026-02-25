# Decision Framework — Extended Matrix

---

## Decision Matrix (4 Criteria)

| Criteria | Source | Check | Pass | Fail |
|---|---|---|---|---|
| Technical Score | Screener Agent `composite_score` | Score threshold | >= 60 | < 60 |
| Sentiment | Analyst Agent `sentiment_label` | Not bearish | BULLISH or NEUTRAL | BEARISH |
| Red Flags | Analyst Agent `red_flags` | No flags present | Empty list `[]` | Any flag present |
| Portfolio Capacity | Portfolio DB `open_positions`, `cash` | Room and funds available | < 5 positions AND sufficient cash | 5 positions OR insufficient cash |

---

## Decision Rules

| Criteria Passing | Decision | Action |
|---|---|---|
| ALL 4 pass | EXECUTE | Proceed to Executor with full position |
| 3 of 4 pass | PROCEED WITH CAUTION | Proceed to Executor with 75% position size |
| 2 or fewer pass | SKIP | Do not trade; log reason |

**Important**: The specific criteria that fails matters:
- If Red Flags is the failing criterion among 3-pass scenarios, it is an AUTOMATIC VETO (see below). Do NOT proceed with caution.
- If Sentiment is BEARISH, it overrides technical signals regardless of score.

---

## Veto Override

Red flags trigger an **AUTOMATIC VETO** regardless of all other criteria.

Even if:
- Technical score is 95
- Sentiment is BULLISH
- Portfolio has full capacity

A single red flag means **SKIP**. No exceptions.

**Red flag examples**:
- SEBI investigation or show-cause notice
- Auditor resignation or qualified opinion
- Promoter pledge increase > 5%
- Fraud allegations from credible sources
- Earnings miss > 10% vs consensus
- Credit rating downgrade
- Key management departure (CEO, CFO)
- Regulatory action against the company

---

## Confidence Levels & Position Sizing

| Confidence | Technical Score | Sentiment | Position Size |
|---|---|---|---|
| HIGH | >= 75 | BULLISH | 100% of calculated max position |
| MODERATE | 60 - 74 | NEUTRAL or BULLISH | 75% of calculated max position |
| LOW | >= 60 | Mixed signals | 50% of calculated max position |

**Calculated max position** = `current_capital * 0.10` (the 10% rule)

**Position size formula**:
```
max_position_value = current_capital * 0.10
adjusted_position_value = max_position_value * confidence_multiplier
quantity = floor(adjusted_position_value / current_price)
```

Where `confidence_multiplier` is:
- HIGH = 1.0
- MODERATE = 0.75
- LOW = 0.50

---

## Worked Examples

### Example 1: Strong BUY

- **Stock**: RELIANCE-EQ
- **Technical score**: 78 (Screener)
- **Sentiment**: BULLISH (Analyst)
- **Red flags**: None (Analyst)
- **Open positions**: 3 of 5
- **Current capital**: Rs.1,00,000

**Evaluation**:
1. Technical >= 60? YES (78)
2. Sentiment not BEARISH? YES (BULLISH)
3. Red flags empty? YES
4. Portfolio capacity? YES (3 < 5, cash available)

**Decision**: ALL 4 pass -> EXECUTE
**Confidence**: HIGH (tech >= 75 AND sentiment BULLISH)
**Position**: 100% of max -> Rs.10,000
**Quantity**: floor(10000 / 2500) = 4 shares
**Stop-loss**: 3% below entry -> Rs.2,425

---

### Example 2: Cautious BUY

- **Stock**: TCS-EQ
- **Technical score**: 65 (Screener)
- **Sentiment**: NEUTRAL (Analyst)
- **Red flags**: None (Analyst)
- **Open positions**: 4 of 5
- **Current capital**: Rs.85,000

**Evaluation**:
1. Technical >= 60? YES (65)
2. Sentiment not BEARISH? YES (NEUTRAL)
3. Red flags empty? YES
4. Portfolio capacity? YES (4 < 5, cash available)

**Decision**: ALL 4 pass -> EXECUTE
**Confidence**: MODERATE (tech 60-74, sentiment NEUTRAL)
**Position**: 75% of max -> Rs.8,500 * 0.75 = Rs.6,375
**Quantity**: floor(6375 / 3400) = 1 share
**Stop-loss**: 3% below entry -> Rs.3,298

---

### Example 3: Veto by Red Flag

- **Stock**: ADANIENT-EQ
- **Technical score**: 82 (Screener)
- **Sentiment**: BULLISH (Analyst)
- **Red flags**: ["SEBI investigation into related-party transactions"] (Analyst)
- **Open positions**: 2 of 5

**Evaluation**:
1. Technical >= 60? YES (82)
2. Sentiment not BEARISH? YES (BULLISH)
3. Red flags empty? NO -> **AUTOMATIC VETO**
4. Portfolio capacity? YES

**Decision**: SKIP (red flag veto override)
**Reasoning**: SEBI investigation is an automatic veto regardless of strong technicals and bullish sentiment.

---

### Example 4: Bearish Sentiment Override

- **Stock**: HDFCBANK-EQ
- **Technical score**: 72 (Screener)
- **Sentiment**: BEARISH (Analyst)
- **Red flags**: None (Analyst)
- **Open positions**: 1 of 5

**Evaluation**:
1. Technical >= 60? YES (72)
2. Sentiment not BEARISH? NO -> Fails
3. Red flags empty? YES
4. Portfolio capacity? YES

**Decision**: 3 of 4 pass -> PROCEED WITH CAUTION? NO. Bearish sentiment is a strong counter-signal. Decision: SKIP.
**Note**: While the matrix says 3-of-4 = caution, bearish sentiment directly contradicts a BUY thesis. The Lead should use judgment here and lean toward SKIP.

---

## Decision Logging

Every decision MUST be logged with:
1. The 4 criteria evaluations (pass/fail with values)
2. The decision outcome (EXECUTE / CAUTION / SKIP)
3. The confidence level and position sizing
4. The reasoning in plain language
5. Any overrides or judgment calls made by the Lead
