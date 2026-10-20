from django.db import models
from tickers.models import Ticker


class Signal(models.Model):
    SIGNAL_DAY_TRADE = "day_trade"
    SIGNAL_MEDIUM = "medium_turnaround"
    SIGNAL_SEASONAL = "seasonal_swing"
    SIGNAL_CHOICES = [
        (SIGNAL_DAY_TRADE, "Day Trade"),
        (SIGNAL_MEDIUM, "Medium Turnaround"),
        (SIGNAL_SEASONAL, "Seasonal Swing"),
    ]

    ACTION_BUY = "BUY"
    ACTION_SELL = "SELL"
    ACTION_HOLD = "HOLD"
    ACTION_TRIM = "TRIM"
    ACTION_CHOICES = [
        (ACTION_BUY, "Buy"),
        (ACTION_SELL, "Sell"),
        (ACTION_HOLD, "Hold"),
        (ACTION_TRIM, "Trim"),
    ]

    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name="signals")
    signal_type = models.CharField(max_length=25, choices=SIGNAL_CHOICES)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    confidence = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    entry_price = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    target_price = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    stop_loss = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    reasoning = models.TextField(blank=True)
    technical_score = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    sentiment_score = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    options_score = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    insider_score = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    seasonal_score = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    ai_expert_report = models.ForeignKey("ai_expert.AIExpertReport", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["ticker", "-created_at"]),
            models.Index(fields=["signal_type", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.ticker.symbol} {self.action} {self.signal_type} ({self.created_at})"


class TechnicalIndicator(models.Model):
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name="technicals")
    timestamp = models.DateTimeField(auto_now_add=True)
    rsi_14 = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    macd = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    macd_signal = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    macd_histogram = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    ema_9 = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    ema_21 = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    ema_50 = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    ema_200 = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    bollinger_upper = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    bollinger_lower = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    bollinger_mid = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    adx = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    atr = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    volume_sma_20 = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["ticker", "-timestamp"]),
        ]

    def __str__(self):
        return f"{self.ticker.symbol} technicals ({self.timestamp})"


class ConfluenceSignal(models.Model):
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name="confluence_signals")
    signal = models.ForeignKey(Signal, on_delete=models.CASCADE, null=True, blank=True)
    vwap_score = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    trend_score = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    momentum_score = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    volume_score = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    all_aligned = models.BooleanField(default=False)
    conviction = models.IntegerField(default=0, help_text="0-100 conviction score")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class RegimeState(models.Model):
    regime = models.CharField(max_length=50)
    strategy_mode = models.CharField(max_length=50)
    vix = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    treasury_10y = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    yield_delta_30d = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    yield_curve = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    spy_trend = models.CharField(max_length=20, blank=True)
    score = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    signals = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.regime} ({self.created_at})"