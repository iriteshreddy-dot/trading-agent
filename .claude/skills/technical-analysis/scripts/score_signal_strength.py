"""
Composite signal scoring for technical analysis.
Takes indicator values and produces a 0-100 score.

Scoring:
  Raw range: -100 to +100
  Normalized: (raw + 100) / 2 = 0-100

Classification:
  80-100: STRONG BUY
  65-79:  BUY
  45-64:  NEUTRAL
  30-44:  SELL
  0-29:   STRONG SELL
"""


def score_rsi(rsi_value: float) -> int:
    """Score RSI indicator (-20 to +20)."""
    if rsi_value < 30:
        return 20  # Oversold → BUY
    elif rsi_value < 45:
        return 10  # Approaching oversold
    elif rsi_value <= 55:
        return 0   # Neutral
    elif rsi_value <= 70:
        return -10  # Approaching overbought
    else:
        return -20  # Overbought → SELL


def score_macd(macd: float, signal: float, histogram: float) -> int:
    """Score MACD indicator (-25 to +25)."""
    score = 0

    # Crossover
    if macd > signal:
        score += 15  # Bullish crossover
    else:
        score -= 15  # Bearish crossover

    # Histogram momentum
    if histogram > 0:
        score += 5
    else:
        score -= 5

    # Zero line
    if macd > 0:
        score += 5
    else:
        score -= 5

    return score


def score_ema_trend(trend: str) -> int:
    """Score EMA trend position (-15 to +15)."""
    scores = {
        "ABOVE_ALL": 15,
        "ABOVE_20_50": 10,
        "ABOVE_20": 5,
        "BELOW_ALL": -15,
    }
    return scores.get(trend, 0)


def score_bollinger(pct_b: float, rsi_value: float) -> int:
    """Score Bollinger Bands position (-10 to +10)."""
    if pct_b < 0.1 and rsi_value < 30:
        return 10  # Near lower band + oversold
    elif pct_b > 0.9 and rsi_value > 70:
        return -10  # Near upper band + overbought
    elif pct_b < 0.2:
        return 5  # Walking lower band area
    elif pct_b > 0.8:
        return -5  # Walking upper band area
    return 0


def score_volume(volume_ratio: float, price_direction: str = "UP") -> int:
    """Score volume analysis (-10 to +10)."""
    if volume_ratio > 2.0:
        return 10 if price_direction == "UP" else -10
    elif volume_ratio > 1.5:
        return 5 if price_direction == "UP" else -5
    elif volume_ratio < 0.5:
        return -10  # Low conviction
    return 0


def compute_composite_score(indicators: dict) -> dict:
    """
    Compute composite score from all indicators.

    Args:
        indicators: Dict from compute_all_indicators()

    Returns:
        Dict with raw_score, composite_score, classification, confidence
    """
    rsi_val = indicators.get("rsi", {}).get("value", 50)
    macd_data = indicators.get("macd", {})
    ema_data = indicators.get("ema", {})
    boll_data = indicators.get("bollinger", {})
    vol_data = indicators.get("volume", {})

    raw = 0
    raw += score_rsi(rsi_val)
    raw += score_macd(
        macd_data.get("macd", 0),
        macd_data.get("signal", 0),
        macd_data.get("histogram", 0),
    )
    raw += score_ema_trend(ema_data.get("trend", ""))
    raw += score_bollinger(boll_data.get("pct_b", 0.5), rsi_val)
    raw += score_volume(vol_data.get("volume_ratio", 1.0))

    # Normalize: -100..+100 → 0..100
    composite = int((raw + 100) / 2)
    composite = max(0, min(100, composite))

    # Classify
    if composite >= 80:
        classification = "STRONG_BUY"
        confidence = "HIGH"
    elif composite >= 65:
        classification = "BUY"
        confidence = "MODERATE"
    elif composite >= 45:
        classification = "NEUTRAL"
        confidence = "LOW"
    elif composite >= 30:
        classification = "SELL"
        confidence = "MODERATE"
    else:
        classification = "STRONG_SELL"
        confidence = "HIGH"

    return {
        "raw_score": raw,
        "composite_score": composite,
        "classification": classification,
        "confidence": confidence,
    }


if __name__ == "__main__":
    import json

    # Example
    example = {
        "rsi": {"value": 32.5},
        "macd": {"macd": 1.2, "signal": 0.8, "histogram": 0.4},
        "ema": {"trend": "ABOVE_20_50"},
        "bollinger": {"pct_b": 0.15},
        "volume": {"volume_ratio": 1.8},
    }
    result = compute_composite_score(example)
    print(json.dumps(result, indent=2))
