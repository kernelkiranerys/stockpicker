from django.contrib import admin
from .models import AIExpertReport


@admin.register(AIExpertReport)
class AIExpertReportAdmin(admin.ModelAdmin):
    list_display = ("ticker", "report_type", "signal_type", "action", "sentiment_score", "confidence", "created_at")
    list_filter = ("report_type", "signal_type", "action")
    search_fields = ("ticker__symbol",)
    date_hierarchy = "created_at"