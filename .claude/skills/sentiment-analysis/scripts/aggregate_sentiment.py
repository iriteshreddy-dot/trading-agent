"""
Aggregate sentiment from multiple sources into a single assessment.
Combines stock-level, sector-level, and market-level sentiment.
"""


def aggregate_sentiment(
    stock_sentiment: dict,
    sector_sentiment: dict | None = None,
    market_sentiment: dict | None = None,
) -> dict:
    """
    Combine multiple sentiment dimensions into final assessment.

    Args:
        stock_sentiment: {score: int, classification: str, red_flags: list}
        sector_sentiment: {score: int, sector: str} (optional)
        market_sentiment: {fii_flow: float, vix: float} (optional)

    Returns:
        Final aggregated sentiment with confidence
    """
    # Stock sentiment has highest weight (60%)
    stock_score = stock_sentiment.get("score", 0)
    stock_weight = 0.6

    # Sector weight (25%)
    sector_score = sector_sentiment.get("score", 0) if sector_sentiment else 0
    sector_weight = 0.25 if sector_sentiment else 0

    # Market weight (15%)
    market_score = 0
    market_weight = 0.15 if market_sentiment else 0
    if market_sentiment:
        fii = market_sentiment.get("fii_flow", 0)
        vix = market_sentiment.get("vix", 15)

        # FII flow scoring
        if fii > 2000:
            market_score += 25
        elif fii > 500:
            market_score += 10
        elif fii < -2000:
            market_score -= 25
        elif fii < -500:
            market_score -= 10

        # VIX scoring
        if vix > 25:
            market_score -= 30  # Extreme fear
        elif vix > 20:
            market_score -= 15
        elif vix < 12:
            market_score -= 5  # Complacency risk

    # Normalize weights
    total_weight = stock_weight + sector_weight + market_weight
    if total_weight > 0:
        final_score = (
            stock_score * stock_weight
            + sector_score * sector_weight
            + market_score * market_weight
        ) / total_weight
    else:
        final_score = stock_score

    final_score = max(-100, min(100, int(final_score)))

    # Red flags always override
    red_flags = stock_sentiment.get("red_flags", [])
    veto = len(red_flags) > 0

    if veto:
        classification = "BEARISH"
        confidence = "HIGH"
    elif final_score >= 75:
        classification = "STRONG_BULLISH"
        confidence = "HIGH"
    elif final_score >= 25:
        classification = "BULLISH"
        confidence = "MODERATE"
    elif final_score >= -24:
        classification = "NEUTRAL"
        confidence = "LOW"
    elif final_score >= -74:
        classification = "BEARISH"
        confidence = "MODERATE"
    else:
        classification = "STRONG_BEARISH"
        confidence = "HIGH"

    return {
        "final_score": final_score,
        "classification": classification,
        "confidence": confidence,
        "veto_active": veto,
        "red_flags": red_flags,
        "components": {
            "stock": stock_score,
            "sector": sector_score,
            "market": market_score,
        },
    }


if __name__ == "__main__":
    import json

    result = aggregate_sentiment(
        stock_sentiment={"score": 65, "classification": "BULLISH", "red_flags": []},
        sector_sentiment={"score": 40, "sector": "Energy"},
        market_sentiment={"fii_flow": -1200, "vix": 14.5},
    )
    print(json.dumps(result, indent=2))
