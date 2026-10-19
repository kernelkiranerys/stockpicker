from django.db import models


class Exchange(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code


class Sector(models.Model):
    name = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Industry(models.Model):
    name = models.CharField(max_length=100, unique=True)
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name="industries")

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "industries"

    def __str__(self):
        return self.name


class Ticker(models.Model):
    symbol = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    exchange = models.ForeignKey(Exchange, on_delete=models.SET_NULL, null=True, blank=True)
    sector = models.ForeignKey(Sector, on_delete=models.SET_NULL, null=True, blank=True)
    industry = models.ForeignKey(Industry, on_delete=models.SET_NULL, null=True, blank=True)
    currency = models.CharField(max_length=10, default="USD")
    yf_suffix = models.CharField(max_length=10, blank=True, help_text="Yahoo Finance exchange suffix, e.g. .L, .DE, .PA")
    is_active = models.BooleanField(default=True)
    last_price = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    last_price_updated = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["symbol"]

    def __str__(self):
        return self.symbol

    @property
    def yf_symbol(self):
        if self.yf_suffix:
            return f"{self.symbol}{self.yf_suffix}"
        return self.symbol


class Watchlist(models.Model):
    name = models.CharField(max_length=100, default="Seasonal Swing")
    description = models.TextField(blank=True)
    tickers = models.ManyToManyField(Ticker, related_name="watchlists")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Holding(models.Model):
    watchlist = models.ForeignKey(Watchlist, on_delete=models.CASCADE, related_name="holdings")
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE)
    shares = models.DecimalField(max_digits=18, decimal_places=6, default=0)
    entry_price = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    entry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("watchlist", "ticker")

    def __str__(self):
        return f"{self.ticker.symbol} ({self.watchlist.name})"