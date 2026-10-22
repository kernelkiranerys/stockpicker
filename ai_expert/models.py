from django.db import models
from tickers.models import Ticker


class AIExpertReport(models.Model):
    REPORT_FAST = "fast"
    REPORT_DEEP = "deep"
    REPORT_CHOICES = [
        (REPORT_FAST, "Fast (7B)"),
        (REPORT_DEEP, "Deep (14B)"),
    ]

    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name="ai_reports")
    report_type = models.CharField(max_length=10, choices=REPORT_CHOICES)
    signal_type = models.CharField(max_length=25, default="seasonal_swing")
    summary = models.TextField(blank=True)
    sentiment_score = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    sentiment_reasoning = models.TextField(blank=True)
    action = models.CharField(max_length=10, default="HOLD")
    action_reasoning = models.TextField(blank=True)
    confidence = models.IntegerField(default=0, help_text="0-100 conviction score")
    conviction = models.IntegerField(default=0, help_text="0-100 conviction for screening threshold")
    confluence_assessment = models.TextField(blank=True)
    lesson_applied = models.TextField(blank=True)
    key_risks = models.JSONField(default=list, blank=True)
    cited_chunks = models.JSONField(default=list, blank=True)
    data_snapshot = models.JSONField(default=dict, blank=True)
    model_name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["ticker", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.ticker.symbol} AI {self.action} ({self.created_at})"