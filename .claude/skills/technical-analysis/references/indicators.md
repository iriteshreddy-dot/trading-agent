# Technical Indicators — Mathematical Formulas

## RSI (Relative Strength Index) — Period: 14

- RS = Average Gain over N periods / Average Loss over N periods
- RSI = 100 - (100 / (1 + RS))
- First calculation: Simple average of gains/losses over 14 periods
- Subsequent: Smoothed using previous average (Wilder's smoothing)
- Formula: Avg Gain = (Prev Avg Gain × 13 + Current Gain) / 14
- Avg Loss = (Prev Avg Loss × 13 + Current Loss) / 14

Interpretation:
- RSI > 70 = Overbought (potential sell signal)
- RSI < 30 = Oversold (potential buy signal)
- RSI 40-60 = Neutral zone

## MACD (12, 26, 9)

- MACD Line = EMA(12) - EMA(26)
- Signal Line = EMA(9) of MACD Line
- Histogram = MACD Line - Signal Line
- EMA formula: EMA = Price × k + EMA_prev × (1-k), where k = 2/(N+1)

Interpretation:
- MACD crosses above Signal = Bullish crossover
- MACD crosses below Signal = Bearish crossover
- Histogram expanding = Trend strengthening
- Histogram contracting = Trend weakening

## Exponential Moving Averages (20, 50, 200)

- EMA formula: EMA_today = Price_today × (2/(N+1)) + EMA_yesterday × (1 - 2/(N+1))
- Requires N+1 data points minimum
- First EMA = SMA of first N periods

Smoothing factors:
- EMA(20): k = 2/21 = 0.0952
- EMA(50): k = 2/51 = 0.0392
- EMA(200): k = 2/201 = 0.00995

Interpretation:
- Price > EMA(20) > EMA(50) > EMA(200) = Strong uptrend
- Price < EMA(20) < EMA(50) < EMA(200) = Strong downtrend
- EMA(50) crossing EMA(200) upward = Golden Cross (bullish)
- EMA(50) crossing EMA(200) downward = Death Cross (bearish)

## Bollinger Bands (20, 2)

- Middle Band = SMA(20)
- Upper Band = SMA(20) + 2 × StdDev(20)
- Lower Band = SMA(20) - 2 × StdDev(20)
- Band Width = (Upper - Lower) / Middle
- %B = (Price - Lower) / (Upper - Lower)

Interpretation:
- Price touching Upper Band = Overbought / strong uptrend
- Price touching Lower Band = Oversold / strong downtrend
- Band squeeze (narrow width) = Low volatility, breakout imminent
- Band expansion = High volatility, trend in progress
- %B > 1 = Price above upper band
- %B < 0 = Price below lower band

## Volume Analysis

- Volume MA = SMA(20) of daily volume
- Volume Ratio = Current Volume / Volume MA
- OBV (On-Balance Volume): Running total, add volume on up days, subtract on down days

Interpretation:
- Volume Ratio > 1.5 = Significant volume (confirms price move)
- Volume Ratio < 0.5 = Low volume (price move may be unreliable)
- Rising OBV with rising price = Trend confirmed
- Divergence between OBV and price = Potential reversal
