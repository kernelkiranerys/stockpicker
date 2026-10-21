from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


def score_text(text):
    """Score social media text using VADER.
    Returns (score, confidence) where score is -1.0 to 1.0
    and confidence is 0.0 to 1.0 based on compound strength.
    """
    if not text or not text.strip():
        return 0.0, 0.0

    scores = _analyzer.polarity_scores(text)
    compound = scores["compound"]

    if abs(compound) >= 0.75:
        confidence = 0.95
    elif abs(compound) >= 0.5:
        confidence = 0.80
    elif abs(compound) >= 0.3:
        confidence = 0.65
    elif abs(compound) >= 0.15:
        confidence = 0.45
    else:
        confidence = 0.20

    return round(compound, 4), round(confidence, 4)


def score_posts(posts):
    """Score a list of Reddit post dicts. Adds 'sentiment' and 'sentiment_confidence' keys."""
    results = []
    for post in posts:
        text = f"{post.get('title', '')} {post.get('body', '')}"
        score, conf = score_text(text)
        post["sentiment"] = score
        post["sentiment_confidence"] = conf
        results.append(post)
    return results