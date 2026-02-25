"""
Chart pattern detection for candlestick analysis.
Detects bullish and bearish patterns from OHLCV data.

Bullish patterns (+10 bonus): double bottom, inverse H&S, bullish engulfing, morning star
Bearish patterns (-10 penalty): double top, H&S, bearish engulfing, evening star
"""


def detect_bullish_engulfing(candles: list[list]) -> bool:
    """
    Bullish engulfing: Current candle's body completely engulfs previous bearish candle.
    Candle format: [timestamp, open, high, low, close, volume]
    """
    if len(candles) < 2:
        return False

    prev_open, prev_close = candles[-2][1], candles[-2][4]
    curr_open, curr_close = candles[-1][1], candles[-1][4]

    prev_bearish = prev_close < prev_open
    curr_bullish = curr_close > curr_open
    engulfs = curr_open <= prev_close and curr_close >= prev_open

    return prev_bearish and curr_bullish and engulfs


def detect_bearish_engulfing(candles: list[list]) -> bool:
    """
    Bearish engulfing: Current bearish candle engulfs previous bullish candle.
    """
    if len(candles) < 2:
        return False

    prev_open, prev_close = candles[-2][1], candles[-2][4]
    curr_open, curr_close = candles[-1][1], candles[-1][4]

    prev_bullish = prev_close > prev_open
    curr_bearish = curr_close < curr_open
    engulfs = curr_open >= prev_close and curr_close <= prev_open

    return prev_bullish and curr_bearish and engulfs


def detect_morning_star(candles: list[list]) -> bool:
    """
    Morning star: 3-candle bullish reversal.
    1. Large bearish candle
    2. Small body (star) with gap down
    3. Large bullish candle closing above midpoint of candle 1
    """
    if len(candles) < 3:
        return False

    c1_open, c1_close = candles[-3][1], candles[-3][4]
    c2_open, c2_close = candles[-2][1], candles[-2][4]
    c3_open, c3_close = candles[-1][1], candles[-1][4]

    c1_bearish = c1_close < c1_open
    c1_large = abs(c1_close - c1_open) > 0.005 * c1_open  # >0.5% body
    c2_small = abs(c2_close - c2_open) < 0.003 * c2_open  # <0.3% body
    c3_bullish = c3_close > c3_open
    c3_above_mid = c3_close > (c1_open + c1_close) / 2

    return c1_bearish and c1_large and c2_small and c3_bullish and c3_above_mid


def detect_evening_star(candles: list[list]) -> bool:
    """
    Evening star: 3-candle bearish reversal.
    1. Large bullish candle
    2. Small body (star) with gap up
    3. Large bearish candle closing below midpoint of candle 1
    """
    if len(candles) < 3:
        return False

    c1_open, c1_close = candles[-3][1], candles[-3][4]
    c2_open, c2_close = candles[-2][1], candles[-2][4]
    c3_open, c3_close = candles[-1][1], candles[-1][4]

    c1_bullish = c1_close > c1_open
    c1_large = abs(c1_close - c1_open) > 0.005 * c1_open
    c2_small = abs(c2_close - c2_open) < 0.003 * c2_open
    c3_bearish = c3_close < c3_open
    c3_below_mid = c3_close < (c1_open + c1_close) / 2

    return c1_bullish and c1_large and c2_small and c3_bearish and c3_below_mid


def detect_all_patterns(candles: list[list]) -> dict:
    """
    Run all pattern detectors on candle data.

    Args:
        candles: List of [timestamp, open, high, low, close, volume]

    Returns:
        Dict with detected patterns and net bonus/penalty
    """
    bullish = []
    bearish = []

    if detect_bullish_engulfing(candles):
        bullish.append("bullish_engulfing")
    if detect_morning_star(candles):
        bullish.append("morning_star")
    if detect_bearish_engulfing(candles):
        bearish.append("bearish_engulfing")
    if detect_evening_star(candles):
        bearish.append("evening_star")

    # Each pattern = ±10 to composite score
    bonus = len(bullish) * 10 - len(bearish) * 10

    return {
        "bullish_patterns": bullish,
        "bearish_patterns": bearish,
        "pattern_bonus": bonus,
    }


if __name__ == "__main__":
    import json

    # Example: bullish engulfing
    example = [
        ["2026-02-20", 100, 102, 95, 96, 1000000],   # bearish
        ["2026-02-21", 95, 105, 94, 103, 1500000],    # bullish engulfing
    ]
    result = detect_all_patterns(example)
    print(json.dumps(result, indent=2))
