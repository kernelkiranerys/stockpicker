from django.contrib import admin
from .models import Portfolio, Position, Trade, EquityPoint


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ("name", "signal_mode", "starting_cash", "cash", "is_active", "created_at")
    list_filter = ("signal_mode", "is_active", "position_sizing")


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("portfolio", "ticker", "quantity", "entry_price", "current_price", "entry_date", "signal_source")
    list_filter = ("portfolio", "signal_source")
    search_fields = ("ticker__symbol",)


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ("portfolio", "ticker", "side", "quantity", "price", "executed_at", "realized_pnl", "signal_source")
    list_filter = ("side", "signal_source", "portfolio")
    search_fields = ("ticker__symbol",)
    date_hierarchy = "executed_at"


@admin.register(EquityPoint)
class EquityPointAdmin(admin.ModelAdmin):
    list_display = ("portfolio", "timestamp", "total_equity", "benchmark_equity", "excess_return")
    list_filter = ("portfolio",)