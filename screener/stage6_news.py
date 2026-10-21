from tickers.models import Ticker
from data.models import NewsArticle
from screener.models import ScreenedUniverse
from decimal import Decimal
from django.utils import timezone as djtz
from datetime import timedelta


def run_news_overlay(tickers, min_negative_threshold=-0.3):
    """Stage 6: News/sentiment overlay.
    Filters out stocks with impending negative catalysts.
    Uses recent news headlines to detect negative sentiment.

    Returns list of tickers that pass (no negative catalyst detected).
    """
    today = djtz.now().date()
    cutoff = djtz.now() - timedelta(days=3)
    passing = []

    for ticker in tickers:
        recent_news = NewsArticle.objects.filter(
            ticker=ticker,
            published_at__gte=cutoff,
        ).order_by("-published_at")[:10]

        negative_count = 0
        negative_keywords = [
            "lawsuit", "investigation", "fraud", "bankrupt", "recall",
            "downgrade", "miss", "warning", "decline", "plunge", "drop",
            "loss", "debt", "restructuring", "delist", "halt", "suspend",
        ]

        detected_negative = []
        for article in recent_news:
            headline_lower = article.headline.lower()
            if any(kw in headline_lower for kw in negative_keywords):
                negative_count += 1
                detected_negative.append(article.headline[:80])

        has_negative_catalyst = negative_count >= 3

        try:
            result = ScreenedUniverse.objects.get(ticker=ticker, screen_date=today)
            if has_negative_catalyst:
                result.notes = (result.notes + "; " if result.notes else "") + \
                    f"Negative catalyst: {detected_negative[0]}"
            result.save()
        except ScreenedUniverse.DoesNotExist:
            pass

        if not has_negative_catalyst:
            passing.append(ticker)

    return passing