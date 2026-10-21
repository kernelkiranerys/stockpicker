from django.db import models
from tickers.models import Ticker


class BacktestRun(models.Model):
    name = models.CharField(max_length=200)
    strategy = models.CharField(max_length=100, help_text="confluence, seasonal, mean_reversion")
    start_date = models.DateField()
    end_date = models.DateField()
    initial_capital = models.DecimalField(max_digits=18, decimal_places=2, default=10000)
    final_value = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    total_return_pct = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    win_rate = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    max_drawdown_pct = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    sharpe_ratio = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    avg_win_pct = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    avg_loss_pct = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    slippage_pct = models.DecimalField(max_digits=8, decimal_places=4, default=0.1)
    commission_pct = models.DecimalField(max_digits=8, decimal_places=4, default=0.1)
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    raw_results = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.strategy}) {self.total_return_pct}%"


class BacktestTrade(models.Model):
    run = models.ForeignKey(BacktestRun, on_delete=models.CASCADE, related_name="trades")
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE)
    side = models.CharField(max_length=10)
    entry_date = models.DateField()
    entry_price = models.DecimalField(max_digits=16, decimal_places=6)
    exit_date = models.DateField(null=True, blank=True)
    exit_price = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    pnl = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    pnl_pct = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    signal_reasoning = models.TextField(blank=True)

    class Meta:
        ordering = ["entry_date"]