from django.db import models
from pgvector.django import VectorField
from tickers.models import Ticker


class SentimentScore(models.Model):
    SOURCE_NEWS = "news"
    SOURCE_REDDIT = "reddit"
    SOURCE_AI = "ai_expert"
    SOURCE_CHOICES = [
        (SOURCE_NEWS, "News"),
        (SOURCE_REDDIT, "Reddit"),
        (SOURCE_AI, "AI Expert"),
    ]

    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name="sentiment_scores")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    score = models.DecimalField(max_digits=6, decimal_places=4, help_text="Sentiment -1.0 to 1.0")
    confidence = models.DecimalField(max_digits=6, decimal_places=4, default=0.5)
    timestamp = models.DateTimeField()
    raw_text = models.TextField(blank=True)
    raw_meta = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["ticker", "source", "-timestamp"]),
        ]

    def __str__(self):
        return f"{self.ticker.symbol} {self.source} {self.score} ({self.timestamp})"


class DailySentimentAggregate(models.Model):
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name="daily_sentiment")
    date = models.DateField()
    news_sentiment = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    reddit_sentiment = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    ai_sentiment = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    composite = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    mention_volume = models.IntegerField(default=0)
    news_count = models.IntegerField(default=0)
    reddit_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ("ticker", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.ticker.symbol} sentiment {self.date} ({self.composite})"