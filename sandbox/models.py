from django.db import models
from django.utils import timezone
from tickers.models import Ticker
from signals.models import Signal


class Portfolio(models.Model):
    SIGNAL_DAY_TRADE = "day_trade"
    SIGNAL_MEDIUM = "medium_turnaround"
    SIGNAL_SEASONAL = "seasonal_swing"
    MODE_CHOICES = [
        (SIGNAL_DAY_TRADE, "Day Trader"),
        (SIGNAL_MEDIUM, "Swing"),
        (SIGNAL_SEASONAL, "Seasonal"),
    ]

    SIZING_CONFIDENCE = "confidence_weighted"
    SIZING_EQUAL = "equal_weight"
    SIZING_FIXED = "fixed_amount"
    SIZING_CHOICES = [
        (SIZING_CONFIDENCE, "Confidence-weighted"),
        (SIZING_EQUAL, "Equal weight"),
        (SIZING_FIXED, "Fixed amount"),
    ]

    name = models.CharField(max_length=100, default="Portfolio")
    signal_mode = models.CharField(max_length=25, choices=MODE_CHOICES)
    starting_cash = models.DecimalField(max_digits=18, decimal_places=2, default=10000)
    cash = models.DecimalField(max_digits=18, decimal_places=2, default=10000)
    position_sizing = models.CharField(max_length=30, choices=SIZING_CHOICES, default=SIZING_CONFIDENCE)
    fees_per_trade = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    benchmark_ticker = models.CharField(max_length=20, default="SPY")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.signal_mode})"

    @property
    def total_value(self):
        positions_value = sum(p.current_value for p in self.positions.all() if p.current_value)
        return float(self.cash) + positions_value

    @property
    def total_pnl(self):
        return self.total_value - float(self.starting_cash)

    @property
    def total_pnl_pct(self):
        if float(self.starting_cash) == 0:
            return 0
        return (self.total_pnl / float(self.starting_cash)) * 100


class Position(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="positions")
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    entry_price = models.DecimalField(max_digits=16, decimal_places=6)
    entry_date = models.DateTimeField()
    entry_signal = models.ForeignKey(Signal, on_delete=models.SET_NULL, null=True, blank=True)
    entry_confidence = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    current_price = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    signal_source = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = ("portfolio", "ticker")

    def __str__(self):
        return f"{self.portfolio.name}: {self.ticker.symbol} x{self.quantity}"

    @property
    def current_value(self):
        if self.current_price:
            return float(self.quantity) * float(self.current_price)
        return float(self.quantity) * float(self.entry_price)

    @property
    def unrealized_pnl(self):
        if self.current_price:
            return float(self.quantity) * (float(self.current_price) - float(self.entry_price))
        return 0

    @property
    def unrealized_pnl_pct(self):
        if float(self.entry_price) == 0:
            return 0
        if self.current_price:
            return ((float(self.current_price) - float(self.entry_price)) / float(self.entry_price)) * 100
        return 0

    @property
    def days_held(self):
        if self.entry_date:
            delta = timezone.now() - self.entry_date
            return delta.days
        return 0


class Trade(models.Model):
    SIDE_BUY = "BUY"
    SIDE_SELL = "SELL"
    SIDE_CHOICES = [
        (SIDE_BUY, "Buy"),
        (SIDE_SELL, "Sell"),
    ]

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="trades")
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE)
    side = models.CharField(max_length=10, choices=SIDE_CHOICES)
    quantity = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    price = models.DecimalField(max_digits=16, decimal_places=6)
    executed_at = models.DateTimeField(auto_now_add=True)
    signal = models.ForeignKey(Signal, on_delete=models.SET_NULL, null=True, blank=True)
    realized_pnl = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    realized_pnl_pct = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reason = models.TextField(blank=True)
    signal_source = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["-executed_at"]

    def __str__(self):
        return f"{self.portfolio.name}: {self.side} {self.ticker.symbol} x{self.quantity} @ {self.price}"


class EquityPoint(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="equity_points")
    timestamp = models.DateTimeField(auto_now_add=True)
    cash = models.DecimalField(max_digits=18, decimal_places=2)
    positions_value = models.DecimalField(max_digits=18, decimal_places=2)
    total_equity = models.DecimalField(max_digits=18, decimal_places=2)
    benchmark_price = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    benchmark_equity = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    portfolio_pnl_pct = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    benchmark_pnl_pct = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    excess_return = models.DecimalField(max_digits=10, decimal_places=4, default=0)

    class Meta:
        ordering = ["timestamp"]
        indexes = [
            models.Index(fields=["portfolio", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.portfolio.name} equity {self.total_equity} ({self.timestamp})"