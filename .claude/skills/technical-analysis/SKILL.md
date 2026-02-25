---
name: technical-analysis
description: Compute and interpret technical indicators for Indian stocks. Use this skill whenever analyzing stock charts, computing RSI/MACD/moving averages, scoring signal strength, detecting chart patterns, or making technical trading assessments. Trigger for any mention of technical analysis, indicators, overbought/oversold, support/resistance, moving average crossovers, or signal scoring for Nifty 50 stocks.
---

# Technical Analysis Skill — Indian Stock Market

## Overview

This skill provides a systematic framework for computing technical indicators and converting them into actionable trading signals for Nifty 50 stocks. It produces a **composite signal score (0-100)** that the orchestrator uses for decision-making.

## Indicator Suite

### 1. RSI (Relative Strength Index) — Period: 14

**Computation:** Run `scripts/compute_indicators.py` with OHLCV data.

**Interpretation:**
- RSI < 30: Oversold → potential BUY signal (+20 to composite score)
- RSI 30-45: Approaching oversold → weak BUY signal (+10)
- RSI 45-55: Neutral zone → no signal (0)
- RSI 55-70: Approaching overbought → weak SELL signal (-10)
- RSI > 70: Overbought → potential SELL signal (-20)

**Divergence (high value signal):**
- Bullish divergence: Price making lower lows, RSI making higher lows → strong BUY (+25)
- Bearish divergence: Price making higher highs, RSI making lower highs → strong SELL (-25)

### 2. MACD (12, 26, 9)

**Interpretation:**
- MACD crosses above signal line → BUY signal (+15)
- MACD crosses below signal line → SELL signal (-15)
- MACD histogram increasing → momentum building (+5)
- MACD histogram decreasing → momentum fading (-5)
- MACD above zero line → bullish bias (+5)
- MACD below zero line → bearish bias (-5)

### 3. Moving Averages

**EMAs used:** 20-day (short), 50-day (medium), 200-day (long)

**Interpretation:**
- Price above all 3 EMAs → strong uptrend (+15)
- Price above 20 & 50, below 200 → medium uptrend (+10)
- Price above 20 only → weak/recovering (+5)
- Price below all 3 EMAs → strong downtrend (-15)
- Golden cross (50 crosses above 200) → major BUY signal (+20)
- Death cross (50 crosses below 200) → major SELL signal (-20)

### 4. Bollinger Bands (20, 2)

**Interpretation:**
- Price touches lower band + RSI oversold → BUY signal (+10)
- Price touches upper band + RSI overbought → SELL signal (-10)
- Band squeeze (narrowing) → breakout imminent, prepare for move (+5 alert)
- Price walking upper band → strong trend, don't short (+5)
- Price walking lower band → strong downtrend, don't buy (-5)

### 5. Volume Analysis

**Interpretation:**
- Volume > 2x 20-day average → unusual activity, confirms signal (+10)
- Volume > 1.5x average → above normal, moderate confirmation (+5)
- Volume < 0.5x average → low conviction, reduce signal confidence (-10)
- Volume increasing on price rise → healthy uptrend (+5)
- Volume increasing on price fall → distribution, bearish (-5)

## Composite Signal Scoring

Run `scripts/score_signal_strength.py` to compute the composite score.

**Score = Sum of all individual indicator scores, normalized to 0-100**

```
Raw score range: -100 to +100
Normalized: (raw + 100) / 2 = 0-100 scale

Signal classification:
  80-100: STRONG BUY — Multiple aligned bullish signals
  65-79:  BUY — Majority bullish, minor concerns
  45-64:  NEUTRAL — Mixed signals, no action
  30-44:  SELL — Majority bearish signals
  0-29:   STRONG SELL — Multiple aligned bearish signals
```

**Decision threshold for the trading system: Score ≥ 60 to flag for deeper analysis.**

## Indian Market-Specific Adjustments

Refer to `references/indian-market-context.md` for detailed guidance on:

- **Circuit limits:** NSE stocks have 5%/10%/20% circuit filters. If a stock hits upper circuit, it may be too late to buy. Lower circuit means no exit possible.
- **Expiry effects:** Options expiry on Thursday can cause unusual price action in Nifty and Bank Nifty stocks. Reduce signal confidence by 20% on expiry days.
- **FII/DII flows:** Large institutional flows can override technical signals. If FII selling > ₹2000 Cr in a day, reduce BUY confidence by 15%.
- **Sector rotation:** When FIIs rotate out of IT into Banking, individual stock technicals may be misleading. Check sector-level trends.
- **T+1 settlement:** Affects position management but not TA computation.

## Pattern Detection

Run `scripts/detect_patterns.py` for chart pattern identification:

**Bullish patterns (bonus +10 to composite):**
- Double bottom
- Inverse head and shoulders
- Bullish engulfing candle
- Morning star

**Bearish patterns (penalty -10 to composite):**
- Double top
- Head and shoulders
- Bearish engulfing candle
- Evening star

## Output Format

Every technical analysis should produce this structured output:

```json
{
  "symbol": "NSE:RELIANCE",
  "timestamp": "2026-02-22T10:30:00+05:30",
  "indicators": {
    "rsi": {"value": 32.5, "signal": "OVERSOLD", "score": 20},
    "macd": {"value": -1.2, "signal": "BEARISH_CROSS", "score": -15},
    "ema_trend": {"position": "ABOVE_20_50", "score": 10},
    "bollinger": {"position": "NEAR_LOWER", "score": 10},
    "volume": {"ratio": 1.8, "signal": "ABOVE_NORMAL", "score": 5}
  },
  "patterns_detected": ["bullish_engulfing"],
  "pattern_bonus": 10,
  "raw_score": 40,
  "composite_score": 70,
  "classification": "BUY",
  "confidence": "MODERATE",
  "notes": "RSI oversold with above-average volume. MACD still bearish — wait for crossover confirmation."
}
```

## Reference Files

- `references/indicators.md` — Full mathematical formulas for each indicator
- `references/indian-market-context.md` — NSE/BSE specific trading nuances
