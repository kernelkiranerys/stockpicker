from django.db import models
from django.utils import timezone
from signals.models import Signal


class SignalLogEntry(models.Model):
    signal = models.ForeignKey(Signal, on_delete=models.CASCADE, related_name="log_entries")
    recorded_at = models.DateTimeField(auto_now_add=True)
    outcome = models.CharField(max_length=20, blank=True, help_text="win/loss/pending")
    pnl_pct = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    days_to_outcome = models.IntegerField(null=True, blank=True)
    entry_price = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    exit_price = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-recorded_at"]

    def __str__(self):
        return f"{self.signal} → {self.outcome} ({self.pnl_pct}%)"