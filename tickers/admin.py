from django.contrib import admin
from .models import Exchange, Sector, Industry, Ticker, Watchlist, Holding


@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "country")
    search_fields = ("code", "name")


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ("name", "parent")
    search_fields = ("name",)


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ("name", "sector")
    list_filter = ("sector",)
    search_fields = ("name",)


@admin.register(Ticker)
class TickerAdmin(admin.ModelAdmin):
    list_display = ("symbol", "name", "exchange", "sector", "industry", "currency", "last_price", "is_active")
    list_filter = ("exchange", "sector", "industry", "is_active")
    search_fields = ("symbol", "name")


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    filter_horizontal = ("tickers",)


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ("watchlist", "ticker", "shares", "entry_price", "entry_date")
    list_filter = ("watchlist",)