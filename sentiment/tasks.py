from celery import shared_task
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from django.utils import timezone as djtz

from tickers.models import Ticker
from data.models import NewsArticle, RedditPost
from sentiment.models import SentimentScore, DailySentimentAggregate


@shared_task
def score_news_sentiment():
    from sentiment.nlp_finbert import score_headline

    articles = NewsArticle.objects.filter(
        sentiment_scores__isnull=True
    ).order_by("-published_at")[:200]

    for article in articles:
        if not article.ticker:
            continue
        text = article.headline
        if article.summary:
            text += f" {article.summary}"
        score, conf = score_headline(text)
        SentimentScore.objects.create(
            ticker=article.ticker,
            source="news",
            score=Decimal(str(score)),
            confidence=Decimal(str(conf)),
            timestamp=article.published_at,
            raw_text=article.headline[:500],
            raw_meta={"url": article.url, "source": article.source},
        )


@shared_task
def score_reddit_sentiment():
    from sentiment.nlp_vader import score_text

    posts = RedditPost.objects.filter(
        sentiment_scores__isnull=True
    ).order_by("-created_at")[:200]

    for post in posts:
        if not post.ticker:
            continue
        text = f"{post.title} {post.body}"
        score, conf = score_text(text)
        SentimentScore.objects.create(
            ticker=post.ticker,
            source="reddit",
            score=Decimal(str(score)),
            confidence=Decimal(str(conf)),
            timestamp=post.created_at,
            raw_text=post.title[:500],
            raw_meta={"subreddit": post.subreddit, "score": post.score},
        )


@shared_task
def aggregate_daily_sentiment():
    today = djtz.now().date()
    tickers = Ticker.objects.filter(is_active=True)

    for ticker in tickers:
        news_scores = SentimentScore.objects.filter(
            ticker=ticker, source="news",
            timestamp__date=today,
        )
        reddit_scores = SentimentScore.objects.filter(
            ticker=ticker, source="reddit",
            timestamp__date=today,
        )
        ai_scores = SentimentScore.objects.filter(
            ticker=ticker, source="ai_expert",
            timestamp__date=today,
        )

        news_avg = _weighted_avg(news_scores)
        reddit_avg = _weighted_avg(reddit_scores)
        ai_avg = _weighted_avg(ai_scores)

        composite = (news_avg * 0.35 + reddit_avg * 0.25 + ai_avg * 0.40) if any([news_avg, reddit_avg, ai_avg]) else 0

        DailySentimentAggregate.objects.update_or_create(
            ticker=ticker,
            date=today,
            defaults={
                "news_sentiment": Decimal(str(round(news_avg, 4))),
                "reddit_sentiment": Decimal(str(round(reddit_avg, 4))),
                "ai_sentiment": Decimal(str(round(ai_avg, 4))),
                "composite": Decimal(str(round(composite, 4))),
                "mention_volume": news_scores.count() + reddit_scores.count(),
                "news_count": news_scores.count(),
                "reddit_count": reddit_scores.count(),
            },
        )


def _weighted_avg(scores_queryset):
    if not scores_queryset.exists():
        return 0.0
    total_weight = 0
    weighted_sum = 0.0
    for s in scores_queryset:
        w = float(s.confidence)
        weighted_sum += float(s.score) * w
        total_weight += w
    return weighted_sum / total_weight if total_weight > 0 else 0.0