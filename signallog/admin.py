from django.contrib import admin
from .models import SignalLogEntry


@admin.register(SignalLogEntry)
class SignalLogEntryAdmin(admin.ModelAdmin):
    list_display = ("signal", "recorded_at", "outcome", "pnl_pct", "days_to_outcome")
    list_filter = ("outcome",)
    search_fields = ("signal__ticker__symbol",)
    date_hierarchy = "recorded_at"