from django.contrib import admin
from .models import SentimentScore, DailySentimentAggregate


@admin.register(SentimentScore)
class SentimentScoreAdmin(admin.ModelAdmin):
    list_display = ("ticker", "source", "score", "confidence", "timestamp")
    list_filter = ("source",)
    search_fields = ("ticker__symbol",)
    date_hierarchy = "timestamp"


@admin.register(DailySentimentAggregate)
class DailySentimentAggregateAdmin(admin.ModelAdmin):
    list_display = ("ticker", "date", "news_sentiment", "reddit_sentiment", "ai_sentiment", "composite", "mention_volume")
    search_fields = ("ticker__symbol",)
    date_hierarchy = "date"