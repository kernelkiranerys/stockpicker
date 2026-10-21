from tickers.models import Ticker
from signals.models import Signal
from screener.models import ScreenedUniverse
from decimal import Decimal
from django.utils import timezone as djtz
from datetime import timedelta


def run_historical_correlation(tickers, min_win_rate=0.55):
    """Stage 3: Check historical signal win rate per stock.
    Backtests each ticker against past signals.
    Excludes stocks with <55% historical win rate.

    Updates ScreenedUniverse records. Returns list that pass.
    """
    today = djtz.now().date()
    passing = []

    for ticker in tickers:
        signals = Signal.objects.filter(ticker=ticker).order_by("-created_at")[:50]

        if signals.count() < 5:
            try:
                result = ScreenedUniverse.objects.get(ticker=ticker, screen_date=today)
                result.historical_win_rate = None
                result.notes = (result.notes + "; " if result.notes else "") + "Insufficient signal history"
                result.save()
            except ScreenedUniverse.DoesNotExist:
                pass
            passing.append(ticker)
            continue

        wins = 0
        total = 0
        for sig in signals:
            entry = float(sig.entry_price) if sig.entry_price else 0
            if entry <= 0:
                continue
            bars_after = list(OHLCV.objects.filter(
                ticker=ticker, interval="1d",
                timestamp__gte=sig.created_at,
            ).order_by("timestamp")[:14])

            if not bars_after:
                continue

            exit_price = float(bars_after[-1].close)
            pnl_pct = (exit_price - entry) / entry * 100

            if sig.action == Signal.ACTION_BUY:
                won = pnl_pct > 0
            elif sig.action in (Signal.ACTION_SELL, Signal.ACTION_TRIM):
                won = pnl_pct < 0
            else:
                continue

            total += 1
            if won:
                wins += 1

        win_rate = wins / total if total > 0 else 0

        try:
            result = ScreenedUniverse.objects.get(ticker=ticker, screen_date=today)
        except ScreenedUniverse.DoesNotExist:
            result = ScreenedUniverse.objects.create(ticker=ticker, screen_date=today)

        result.historical_win_rate = Decimal(str(round(win_rate, 4)))
        result.save()

        if win_rate >= min_win_rate or total < 3:
            passing.append(ticker)

    return passing


from data.models import OHLCV