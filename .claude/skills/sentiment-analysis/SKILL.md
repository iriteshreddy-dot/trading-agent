---
name: sentiment-analysis
description: Gather and score market sentiment from Indian financial news sources, FII/DII data, and corporate actions. Use this skill whenever evaluating news impact on stocks, scoring market sentiment, checking institutional fund flows, analyzing earnings announcements, or assessing sector-level sentiment. Trigger for any mention of news, sentiment, FII, DII, corporate actions, earnings, or market mood for Indian stocks.
---

# Sentiment Analysis Skill — Indian Stock Market

## Overview

This skill provides a systematic framework for gathering news, scoring sentiment, and assessing how external factors might impact trading decisions for Nifty 50 stocks. Sentiment scores complement technical analysis — they don't replace it.

## Sentiment Scoring Framework

### Score Scale: -100 to +100

```
+75 to +100: STRONG BULLISH — Major positive catalyst (earnings beat, upgrade, deal)
+25 to +74:  BULLISH — Positive news flow, favorable sentiment
-24 to +24:  NEUTRAL — No significant sentiment driver
-74 to -25:  BEARISH — Negative news flow, concerns emerging
-100 to -75: STRONG BEARISH — Major negative catalyst (scandal, downgrade, loss)
```

## News Source Priority

1. **NSE/BSE Official Announcements** (highest weight) — Corporate filings, board decisions
2. **RBI/SEBI Regulatory Updates** — Policy changes, rate decisions
3. **Major Financial Dailies** — Economic Times, Mint, Business Standard
4. **Business News Portals** — MoneyControl, NDTV Profit, Ticker
5. **Social Media/Forums** (lowest weight, highest noise) — Twitter/X financial accounts

## What to Analyze

### Stock-Level Sentiment
- Earnings results (beat/miss expectations)
- Management commentary and guidance
- Analyst upgrades/downgrades
- Insider buying/selling (bulk/block deals)
- Corporate actions (dividends, buybacks, splits, rights issues)
- Legal/regulatory issues
- Partnership/contract announcements

### Sector-Level Sentiment
- Regulatory policy changes affecting the sector
- Global peer performance (US tech earnings → Indian IT stocks)
- Commodity price impact (crude oil → OMCs, metals → Tata Steel)
- Currency impact (USD/INR → IT exporters, importers)

### Market-Level Sentiment
- FII/DII flow data (daily net buy/sell)
  - FII selling > ₹2000 Cr → market-wide bearish pressure
  - FII buying > ₹2000 Cr → market-wide bullish support
  - DII buying during FII selling → domestic absorption (less bearish)
- RBI monetary policy (rate cuts → bullish, rate hikes → bearish)
- Global cues (US Fed, China data, crude oil, gold)
- India VIX level (>20 = high fear, <12 = complacency)

## Time Decay on News

News impact decays over time. Apply these multipliers:

| News Age | Multiplier | Reasoning |
|----------|-----------|-----------|
| < 1 hour | 1.0x | Fresh, full impact |
| 1-6 hours | 0.8x | Market partially priced in |
| 6-24 hours | 0.5x | Largely priced in |
| 1-3 days | 0.2x | Residual impact only |
| > 3 days | 0.0x | Fully priced in, ignore |

**Exception:** Structural news (regulatory changes, management fraud) has longer impact. Don't apply time decay to these.

## Red Flags (Override Technical Signals)

If ANY of these are detected, sentiment VETOES a BUY regardless of technical score:

- SEBI investigation or show-cause notice
- Auditor resignation or qualified opinion
- Promoter pledge increase >50% of holdings
- Bulk deal showing major investor exit
- Earnings miss by >20% of consensus
- Management guidance cut
- Debt rating downgrade

## Output Format

```json
{
  "symbol": "NSE:RELIANCE",
  "timestamp": "2026-02-22T10:30:00+05:30",
  "stock_sentiment": {
    "score": 65,
    "classification": "BULLISH",
    "key_drivers": [
      "Q3 earnings beat estimates by 12%",
      "Jio subscriber additions accelerating"
    ],
    "red_flags": [],
    "news_count": 8,
    "freshest_news_age_hours": 2
  },
  "sector_sentiment": {
    "sector": "Energy/Telecom",
    "score": 40,
    "notes": "Crude oil rising — mixed for Reliance (refining +, cost -)"
  },
  "market_sentiment": {
    "fii_flow_today_cr": -1200,
    "dii_flow_today_cr": 800,
    "india_vix": 14.5,
    "global_cues": "US markets flat, no major triggers"
  },
  "final_sentiment": "BULLISH",
  "confidence": "HIGH",
  "veto_active": false
}
```

## Reference Files

- `references/news-sources.md` — API endpoints and data sources for Indian financial news
- `references/sentiment-scoring.md` — Detailed scoring rubric with examples
