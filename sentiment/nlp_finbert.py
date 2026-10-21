from transformers import pipeline as hf_pipeline
from decimal import Decimal

_model = None
_pipeline = None


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = hf_pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            tokenizer="ProsusAI/finbert",
            return_all_scores=True,
        )
    return _pipeline


def score_headline(text):
    """Score a financial news headline using FinBERT.
    Returns (score, confidence) where score is -1.0 to 1.0
    (positive=negative - neutral weight) and confidence is 0.0 to 1.0.
    """
    if not text or not text.strip():
        return 0.0, 0.0

    try:
        pipe = _get_pipeline()
        results = pipe(text[:512])
        scores = {r["label"]: r["score"] for r in results[0]}
        positive = scores.get("positive", 0)
        negative = scores.get("negative", 0)
        neutral = scores.get("neutral", 0)
        score = positive - negative
        confidence = max(positive, negative, neutral)
        return round(score, 4), round(confidence, 4)
    except Exception:
        from sentiment.nlp_vader import score_text
        return score_text(text)


def score_articles(articles):
    """Score a list of news article dicts. Adds 'sentiment' and 'sentiment_confidence' keys."""
    results = []
    for art in articles:
        text = art.get("headline", "")
        if art.get("summary"):
            text += f" {art['summary']}"
        score, conf = score_headline(text)
        art["sentiment"] = score
        art["sentiment_confidence"] = conf
        results.append(art)
    return results