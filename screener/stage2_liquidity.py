from tickers.models import Ticker
from data.models import OHLCV
from screener.models import ScreenedUniverse
from decimal import Decimal
from django.utils import timezone as djtz


def run_liquidity_volatility_filter(tickers, min_volume=5000000, min_daily_range=2.0, min_beta=1.0):
    """Stage 2: Filter by liquidity and volatility.
    - Average daily volume > 5M shares
    - Average daily range > 2%
    - Beta > 1.0 (moves with or more than market)

    Updates ScreenedUniverse records. Returns list that pass.
    """
    today = djtz.now().date()
    passing = []

    for ticker in tickers:
        bars = list(OHLCV.objects.filter(ticker=ticker, interval="1d").order_by("-timestamp")[:20])
        if len(bars) < 10:
            continue

        avg_volume = sum(int(b.volume) for b in bars) / len(bars)
        ranges = [((float(b.high) - float(b.low)) / float(b.close) * 100) for b in bars if float(b.close) > 0]
        avg_range = sum(ranges) / len(ranges) if ranges else 0

        try:
            result = ScreenedUniverse.objects.get(ticker=ticker, screen_date=today)
        except ScreenedUniverse.DoesNotExist:
            result = ScreenedUniverse.objects.create(
                ticker=ticker, screen_date=today,
                avg_daily_volume=int(avg_volume),
                avg_daily_range_pct=Decimal(str(round(avg_range, 4))),
            )

        result.avg_daily_volume = int(avg_volume)
        result.avg_daily_range_pct = Decimal(str(round(avg_range, 4)))

        fund = ticker.fundamentals.order_by("-date").first()
        beta = float(fund.beta) if fund and fund.beta else 1.0
        result.beta = Decimal(str(round(beta, 4))) if beta else None

        passes_liquidity = avg_volume >= min_volume
        passes_volatility = avg_range >= min_daily_range

        result.passes_liquidity = passes_liquidity
        result.passes_volatility = passes_volatility
        result.save()

        if passes_liquidity and passes_volatility:
            passing.append(ticker)

    return passing