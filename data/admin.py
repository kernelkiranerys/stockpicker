from django.contrib import admin
from .models import OHLCV, Fundamental, NewsArticle, RedditPost, InsiderTrade, InstitutionalHolding, OptionsSnapshot, MacroIndicator


@admin.register(OHLCV)
class OHLCVAdmin(admin.ModelAdmin):
    list_display = ("ticker", "timestamp", "interval", "close", "volume")
    list_filter = ("interval", "ticker__exchange")
    search_fields = ("ticker__symbol",)
    date_hierarchy = "timestamp"


@admin.register(Fundamental)
class FundamentalAdmin(admin.ModelAdmin):
    list_display = ("ticker", "date", "pe_ratio", "peg_ratio", "market_cap", "dividend_yield")
    search_fields = ("ticker__symbol",)
    date_hierarchy = "date"


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ("headline", "ticker", "source", "published_at")
    search_fields = ("headline", "ticker__symbol")
    date_hierarchy = "published_at"


@admin.register(RedditPost)
class RedditPostAdmin(admin.ModelAdmin):
    list_display = ("title", "subreddit", "score", "num_comments", "created_at")
    list_filter = ("subreddit",)
    search_fields = ("title", "body", "ticker__symbol")


@admin.register(InsiderTrade)
class InsiderTradeAdmin(admin.ModelAdmin):
    list_display = ("ticker", "insider_name", "title", "transaction_type", "shares", "value", "filing_date")
    list_filter = ("transaction_type",)
    search_fields = ("ticker__symbol", "insider_name")
    date_hierarchy = "filing_date"


@admin.register(InstitutionalHolding)
class InstitutionalHoldingAdmin(admin.ModelAdmin):
    list_display = ("ticker", "filer_name", "shares", "value", "change_pct", "filing_date")
    search_fields = ("ticker__symbol", "filer_name")
    date_hierarchy = "filing_date"


@admin.register(OptionsSnapshot)
class OptionsSnapshotAdmin(admin.ModelAdmin):
    list_display = ("ticker", "expiry", "put_call_ratio", "vol_oi_ratio", "implied_volatility", "unusual_activity")
    list_filter = ("unusual_activity",)


@admin.register(MacroIndicator)
class MacroIndicatorAdmin(admin.ModelAdmin):
    list_display = ("name", "value", "date", "source")
    search_fields = ("name",)
    date_hierarchy = "date"