from celery import shared_task
from django.conf import settings
from tickers.models import Ticker, Watchlist
from ai_expert.expert_runner import run_expert


@shared_task
def run_expert_batch():
    """Hourly fast batch: run 7B expert on screener universe."""
    tickers = Ticker.objects.filter(is_active=True)[:100]
    model = settings.OLLAMA_MODEL_FAST
    for ticker in tickers:
        try:
            run_expert(ticker, "day_trade", model=model)
        except Exception as e:
            print(f"AI expert error for {ticker.symbol}: {e}")


@shared_task
def run_expert_deep():
    """Daily deep dive: run 14B expert on watchlist tickers only."""
    wl = Watchlist.objects.filter(is_active=True).first()
    if not wl:
        return
    model = settings.OLLAMA_MODEL_DEEP
    for ticker in wl.tickers.all():
        try:
            run_expert(ticker, "seasonal_swing", model=model)
        except Exception as e:
            print(f"AI expert deep error for {ticker.symbol}: {e}")