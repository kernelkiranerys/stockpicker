from celery import shared_task
from backtest.engine import run_backtest
from tickers.models import Ticker
from datetime import date, timedelta


@shared_task
def run_weekly_backtest():
    """Weekly: backtest recent confluence signals."""
    end = date.today()
    start = end - timedelta(days=90)

    tickers = list(Ticker.objects.filter(is_active=True))
    run = run_backtest(
        name=f"Weekly Backtest {end}",
        strategy="confluence",
        tickers=tickers,
        start_date=start,
        end_date=end,
        initial_capital=10000,
    )
    return {"run_id": run.id, "return_pct": str(run.total_return_pct)}


@shared_task
def run_seasonal_backtest():
    """Backtest seasonal swing strategy on watchlist tickers."""
    from tickers.models import Watchlist
    end = date.today()
    start = end - timedelta(days=365)

    wl = Watchlist.objects.filter(is_active=True).first()
    if not wl:
        return
    tickers = list(wl.tickers.all())
    run = run_backtest(
        name=f"Seasonal Backtest {end}",
        strategy="seasonal_swing",
        tickers=tickers,
        start_date=start,
        end_date=end,
        initial_capital=10000,
    )
    return {"run_id": run.id, "return_pct": str(run.total_return_pct)}