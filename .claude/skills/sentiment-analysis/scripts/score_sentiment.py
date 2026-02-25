"""
Score sentiment from news headlines.
Uses keyword matching and heuristics for sentiment classification.

Scale: -100 (strong bearish) to +100 (strong bullish)
"""

# Bullish keywords and their base scores
BULLISH_KEYWORDS = {
    "earnings beat": 50,
    "profit surge": 45,
    "revenue growth": 35,
    "upgrade": 25,
    "outperform": 25,
    "overweight": 25,
    "strong results": 40,
    "record profit": 50,
    "dividend": 15,
    "buyback": 20,
    "expansion": 20,
    "partnership": 15,
    "contract win": 25,
    "market share": 20,
    "guidance raise": 40,
    "beat estimates": 45,
    "positive outlook": 30,
    "bullish": 20,
}

# Bearish keywords and their base scores (negative)
BEARISH_KEYWORDS = {
    "earnings miss": -50,
    "profit decline": -40,
    "revenue fall": -35,
    "downgrade": -25,
    "underperform": -25,
    "underweight": -25,
    "weak results": -40,
    "loss widened": -50,
    "sebi investigation": -70,
    "sebi probe": -70,
    "auditor resign": -70,
    "pledge": -40,
    "debt concern": -30,
    "rating downgrade": -35,
    "guidance cut": -45,
    "miss estimates": -45,
    "negative outlook": -30,
    "bearish": -20,
    "fraud": -80,
    "scam": -80,
}

# Red flag keywords (trigger veto)
RED_FLAGS = [
    "sebi investigation",
    "sebi probe",
    "show-cause notice",
    "auditor resign",
    "auditor quit",
    "promoter pledge",
    "bulk deal exit",
    "earnings miss",
    "guidance cut",
    "debt downgrade",
    "rating downgrade",
    "fraud",
    "scam",
]


def score_headline(headline: str) -> dict:
    """
    Score a single news headline.

    Returns:
        {score: int, keywords_matched: list, is_red_flag: bool}
    """
    text = headline.lower()
    total_score = 0
    matched = []
    red_flag = False

    for keyword, score in BULLISH_KEYWORDS.items():
        if keyword in text:
            total_score += score
            matched.append(keyword)

    for keyword, score in BEARISH_KEYWORDS.items():
        if keyword in text:
            total_score += score  # score is already negative
            matched.append(keyword)

    for flag in RED_FLAGS:
        if flag in text:
            red_flag = True
            break

    # Clamp to -100..+100
    total_score = max(-100, min(100, total_score))

    return {
        "score": total_score,
        "keywords_matched": matched,
        "is_red_flag": red_flag,
    }


def apply_time_decay(score: float, age_hours: float) -> float:
    """Apply time decay multiplier to a sentiment score."""
    if age_hours < 1:
        return score * 1.0
    elif age_hours < 6:
        return score * 0.8
    elif age_hours < 24:
        return score * 0.5
    elif age_hours < 72:
        return score * 0.2
    else:
        return 0.0


def aggregate_scores(scored_headlines: list[dict]) -> dict:
    """
    Aggregate multiple headline scores into a final sentiment.

    Returns:
        {final_score, classification, red_flags_found, headline_count}
    """
    if not scored_headlines:
        return {
            "final_score": 0,
            "classification": "NEUTRAL",
            "red_flags_found": False,
            "headline_count": 0,
        }

    scores = [h["score"] for h in scored_headlines]
    red_flags = any(h.get("is_red_flag") for h in scored_headlines)

    avg = sum(scores) / len(scores)
    final = max(-100, min(100, int(avg)))

    if red_flags:
        classification = "BEARISH"  # Red flags override
    elif final >= 75:
        classification = "STRONG_BULLISH"
    elif final >= 25:
        classification = "BULLISH"
    elif final >= -24:
        classification = "NEUTRAL"
    elif final >= -74:
        classification = "BEARISH"
    else:
        classification = "STRONG_BEARISH"

    return {
        "final_score": final,
        "classification": classification,
        "red_flags_found": red_flags,
        "headline_count": len(scored_headlines),
    }


if __name__ == "__main__":
    import json

    examples = [
        "Reliance Q3 earnings beat estimates by 12%, revenue growth strong",
        "SEBI investigation into promoter dealings raises concerns",
        "Company announces special dividend of Rs 10 per share",
    ]
    for headline in examples:
        result = score_headline(headline)
        print(f"'{headline[:50]}...' → {json.dumps(result)}")
