from django.contrib import admin
from .models import Signal, TechnicalIndicator


@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    list_display = ("ticker", "signal_type", "action", "confidence", "is_active", "created_at")
    list_filter = ("signal_type", "action", "is_active")
    search_fields = ("ticker__symbol",)
    date_hierarchy = "created_at"


@admin.register(TechnicalIndicator)
class TechnicalIndicatorAdmin(admin.ModelAdmin):
    list_display = ("ticker", "timestamp", "rsi_14", "macd", "adx")
    search_fields = ("ticker__symbol",)