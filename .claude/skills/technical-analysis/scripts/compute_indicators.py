"""
Compute technical indicators from OHLCV data.
Computes RSI, MACD, EMA, Bollinger Bands, and Volume analysis.

Input: List of [timestamp, open, high, low, close, volume] candles
Output: Dict of indicator values with signals
"""

import math


def compute_rsi(closes: list[float], period: int = 14) -> float:
    """
    Compute RSI (Relative Strength Index).

    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss over N periods
    """
    if len(closes) < period + 1:
        return 50.0  # neutral if insufficient data

    gains = []
    losses = []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))

    # First average: simple
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # Smoothed (Wilder's method)
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def compute_ema(values: list[float], period: int) -> list[float]:
    """
    Compute Exponential Moving Average.

    EMA = Price * k + EMA_prev * (1 - k), where k = 2 / (period + 1)
    """
    if len(values) < period:
        return []

    k = 2 / (period + 1)
    ema = [sum(values[:period]) / period]  # SMA as seed

    for price in values[period:]:
        ema.append(price * k + ema[-1] * (1 - k))

    return ema


def compute_macd(
    closes: list[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> dict:
    """
    Compute MACD (Moving Average Convergence Divergence).

    MACD Line = EMA(12) - EMA(26)
    Signal Line = EMA(9) of MACD Line
    Histogram = MACD Line - Signal Line
    """
    if len(closes) < slow + signal:
        return {"macd": 0, "signal": 0, "histogram": 0}

    ema_fast = compute_ema(closes, fast)
    ema_slow = compute_ema(closes, slow)

    # Align lengths
    offset = len(ema_fast) - len(ema_slow)
    macd_line = [f - s for f, s in zip(ema_fast[offset:], ema_slow)]

    signal_line = compute_ema(macd_line, signal)
    if not signal_line:
        return {"macd": macd_line[-1] if macd_line else 0, "signal": 0, "histogram": 0}

    histogram = macd_line[-1] - signal_line[-1]

    return {
        "macd": round(macd_line[-1], 4),
        "signal": round(signal_line[-1], 4),
        "histogram": round(histogram, 4),
    }


def compute_bollinger(
    closes: list[float], period: int = 20, std_dev: int = 2
) -> dict:
    """
    Compute Bollinger Bands.

    Middle = SMA(20)
    Upper = Middle + 2 * StdDev(20)
    Lower = Middle - 2 * StdDev(20)
    """
    if len(closes) < period:
        return {"upper": 0, "middle": 0, "lower": 0, "pct_b": 0.5}

    window = closes[-period:]
    middle = sum(window) / period
    variance = sum((x - middle) ** 2 for x in window) / period
    std = math.sqrt(variance)

    upper = middle + std_dev * std
    lower = middle - std_dev * std

    current = closes[-1]
    pct_b = (current - lower) / (upper - lower) if upper != lower else 0.5

    return {
        "upper": round(upper, 2),
        "middle": round(middle, 2),
        "lower": round(lower, 2),
        "pct_b": round(pct_b, 4),
    }


def compute_volume_analysis(volumes: list[float], period: int = 20) -> dict:
    """
    Analyze volume relative to moving average.
    """
    if len(volumes) < period:
        return {"volume_ma": 0, "volume_ratio": 1.0, "signal": "NORMAL"}

    vol_ma = sum(volumes[-period:]) / period
    current = volumes[-1]
    ratio = current / vol_ma if vol_ma > 0 else 1.0

    if ratio > 2.0:
        signal = "UNUSUAL_HIGH"
    elif ratio > 1.5:
        signal = "ABOVE_NORMAL"
    elif ratio < 0.5:
        signal = "LOW"
    else:
        signal = "NORMAL"

    return {
        "volume_ma": round(vol_ma, 0),
        "volume_ratio": round(ratio, 2),
        "signal": signal,
    }


def compute_all_indicators(candles: list[list]) -> dict:
    """
    Compute all technical indicators from OHLCV candles.

    Args:
        candles: List of [timestamp, open, high, low, close, volume]

    Returns:
        Dict with all indicator values and signals
    """
    closes = [c[4] for c in candles]
    volumes = [c[5] for c in candles]

    rsi = compute_rsi(closes)
    macd = compute_macd(closes)
    ema_20 = compute_ema(closes, 20)
    ema_50 = compute_ema(closes, 50)
    ema_200 = compute_ema(closes, 200)
    bollinger = compute_bollinger(closes)
    volume = compute_volume_analysis(volumes)

    current_price = closes[-1]

    # EMA trend position
    ema_trend = "BELOW_ALL"
    if ema_20 and current_price > ema_20[-1]:
        ema_trend = "ABOVE_20"
        if ema_50 and current_price > ema_50[-1]:
            ema_trend = "ABOVE_20_50"
            if ema_200 and current_price > ema_200[-1]:
                ema_trend = "ABOVE_ALL"

    return {
        "rsi": {"value": round(rsi, 2)},
        "macd": macd,
        "ema": {
            "ema_20": round(ema_20[-1], 2) if ema_20 else None,
            "ema_50": round(ema_50[-1], 2) if ema_50 else None,
            "ema_200": round(ema_200[-1], 2) if ema_200 else None,
            "trend": ema_trend,
        },
        "bollinger": bollinger,
        "volume": volume,
        "current_price": current_price,
    }


if __name__ == "__main__":
    # Example with dummy data
    import json

    dummy_candles = [
        ["2026-02-20", 100, 105, 98, 102, 1000000],
        ["2026-02-21", 102, 108, 101, 107, 1200000],
        ["2026-02-22", 107, 110, 105, 109, 1500000],
    ]
    print("Note: Need 50+ candles for meaningful indicators.")
    print("This is a stub demonstration.")
    print(json.dumps({"example_output_format": compute_all_indicators(dummy_candles)}, indent=2))
