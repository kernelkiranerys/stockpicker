from sentiment.models import DailySentimentAggregate
from decimal import Decimal


def score_sentiment_trend(ticker, days=14):
    """Analyze sentiment trend over the past N days.
    Returns dict with score (-1 to 1), slope, and signals.
    """
    aggregates = DailySentimentAggregate.objects.filter(
        ticker=ticker
    ).order_by("-date")[:days]

    if not aggregates.exists():
        return {"score": 0, "signals": [], "slope": 0}

    composites = [float(a.composite) for a in reversed(aggregates)]
    if len(composites) < 2:
        return {"score": composites[0] if composites else 0, "signals": ["Insufficient data for trend"], "slope": 0}

    n = len(composites)
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(composites) / n

    numerator = sum((x[i] - x_mean) * (composites[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
    slope = numerator / denominator if denominator > 0 else 0

    current = composites[-1]
    avg = sum(composites) / n

    signals = []
    score = current * 0.5 + slope * 10 * 0.5
    score = max(-1.0, min(1.0, score))

    if slope > 0.05:
        signals.append(f"Sentiment improving (slope={slope:.4f})")
    elif slope < -0.05:
        signals.append(f"Sentiment declining (slope={slope:.4f})")
    else:
        signals.append(f"Sentiment stable (slope={slope:.4f})")

    if current > 0.3:
        signals.append(f"Currently positive sentiment ({current:.2f})")
    elif current < -0.3:
        signals.append(f"Currently negative sentiment ({current:.2f})")

    return {
        "score": round(score, 4),
        "signals": signals,
        "slope": round(slope, 6),
        "current": round(current, 4),
        "average": round(avg, 4),
    }