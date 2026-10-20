from django.db import models
from tickers.models import Ticker


class OHLCV(models.Model):
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name="ohlcv")
    timestamp = models.DateTimeField()
    interval = models.CharField(max_length=10, default="1d")
    open = models.DecimalField(max_digits=16, decimal_places=6)
    high = models.DecimalField(max_digits=16, decimal_places=6)
    low = models.DecimalField(max_digits=16, decimal_places=6)
    close = models.DecimalField(max_digits=16, decimal_places=6)
    volume = models.BigIntegerField(default=0)
    source = models.CharField(max_length=50, default="yfinance")

    class Meta:
        unique_together = ("ticker", "timestamp", "interval")
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["ticker", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.ticker.symbol} {self.timestamp} {self.close}"


class Fundamental(models.Model):
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name="fundamentals")
    date = models.DateField()
    market_cap = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    pe_ratio = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    forward_pe = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    peg_ratio = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    ps_ratio = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    pb_ratio = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    debt_to_equity = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    current_ratio = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    quick_ratio = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    revenue_growth = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    earnings_growth = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    profit_margin = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    free_cash_flow = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    dividend_yield = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    beta = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    raw_info = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ("ticker", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.ticker.symbol} fundamentals {self.date}"


class NewsArticle(models.Model):
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name="news", null=True, blank=True)
    headline = models.TextField()
    summary = models.TextField(blank=True)
    url = models.URLField(blank=True)
    source = models.CharField(max_length=100, blank=True)
    published_at = models.DateTimeField()
    fetched_at = models.DateTimeField(auto_now_add=True)
    raw = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-published_at"]
        indexes = [
            models.Index(fields=["ticker", "-published_at"]),
        ]

    def __str__(self):
        return self.headline[:80]


class RedditPost(models.Model):
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name="reddit_posts", null=True, blank=True)
    subreddit = models.CharField(max_length=50)
    post_id = models.CharField(max_length=20, unique=True)
    title = models.TextField()
    body = models.TextField(blank=True)
    score = models.IntegerField(default=0)
    num_comments = models.IntegerField(default=0)
    created_at = models.DateTimeField()
    fetched_at = models.DateTimeField(auto_now_add=True)
    url = models.URLField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["ticker", "-created_at"]),
        ]

    def __str__(self):
        return f"r/{self.subreddit}: {self.title[:80]}"


class InsiderTrade(models.Model):
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name="insider_trades")
    filing_date = models.DateField()
    trade_date = models.DateField(null=True, blank=True)
    insider_name = models.CharField(max_length=200)
    title = models.CharField(max_length=200, blank=True)
    transaction_type = models.CharField(max_length=20)
    shares = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    price = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    value = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    shares_owned = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    filing_url = models.URLField(blank=True)
    raw = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-filing_date"]
        indexes = [
            models.Index(fields=["ticker", "-filing_date"]),
        ]

    def __str__(self):
        return f"{self.ticker.symbol} {self.transaction_type} {self.shares} ({self.filing_date})"


class InstitutionalHolding(models.Model):
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name="institutional_holdings")
    filing_date = models.DateField()
    filer_name = models.CharField(max_length=300)
    shares = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    value = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    change_shares = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    change_pct = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    filing_url = models.URLField(blank=True)
    raw = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-filing_date"]
        indexes = [
            models.Index(fields=["ticker", "-filing_date"]),
        ]

    def __str__(self):
        return f"{self.ticker.symbol} 13F {self.filer_name} ({self.filing_date})"


class OptionsSnapshot(models.Model):
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name="options_snapshots")
    timestamp = models.DateTimeField(auto_now_add=True)
    expiry = models.DateField()
    call_volume = models.BigIntegerField(default=0)
    put_volume = models.BigIntegerField(default=0)
    call_open_interest = models.BigIntegerField(default=0)
    put_open_interest = models.BigIntegerField(default=0)
    put_call_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    vol_oi_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    implied_volatility = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    iv_percentile = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    iv_skew = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    unusual_activity = models.BooleanField(default=False)
    raw = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["ticker", "-timestamp"]),
        ]

    def __str__(self):
        return f"{self.ticker.symbol} options {self.expiry} ({self.timestamp})"


class MacroIndicator(models.Model):
    name = models.CharField(max_length=100, unique=True)
    value = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    date = models.DateField()
    source = models.CharField(max_length=50, default="FRED")
    raw = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.name} {self.date}"