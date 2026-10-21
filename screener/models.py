from django.db import models
from tickers.models import Ticker


class ScreenedUniverse(models.Model):
    """The tradable universe after fundamental screening (Stage 1)."""
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name="screening_results")
    screen_date = models.DateField()
    market_cap = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    eps = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    pe_ratio = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    beta = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    avg_daily_volume = models.BigIntegerField(default=0)
    avg_daily_range_pct = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    passes_fundamental = models.BooleanField(default=False)
    passes_liquidity = models.BooleanField(default=False)
    passes_volatility = models.BooleanField(default=False)
    historical_win_rate = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    conviction_score = models.IntegerField(default=0, help_text="0-100 AI conviction")
    rank = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    raw = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-screen_date", "-rank"]
        unique_together = ("ticker", "screen_date")
        indexes = [
            models.Index(fields=["screen_date", "-rank"]),
        ]

    def __str__(self):
        return f"{self.ticker.symbol} screen {self.screen_date} rank={self.rank}"


class RegimeSnapshot(models.Model):
    """Daily market regime snapshot."""
    date = models.DateField(unique=True)
    regime = models.CharField(max_length=50)
    strategy_mode = models.CharField(max_length=50)
    vix = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    treasury_10y = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    yield_delta_30d = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    yield_curve = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    spy_trend = models.CharField(max_length=20, blank=True)
    score = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    signals = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.regime} {self.date}"