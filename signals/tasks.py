from celery import shared_task
from tickers.models import Ticker, Watchlist
from signals.engine_confluence import generate_confluence_signal
from signals.engine_regime import detect_regime
from signals.engine_seasonal import compute_seasonal_pattern
from signals.models import RegimeState


@shared_task
def compute_technicals():
    from signals.engine_technical import compute_technicals as compute
    from data.models import OHLCV
    from signals.models import TechnicalIndicator

    for ticker in Ticker.objects.filter(is_active=True):
        ohlcv_qs = OHLCV.objects.filter(ticker=ticker, interval="1d").order_by("-timestamp")[:250]
        tech_data = compute(ohlcv_qs)
        if tech_data:
            TechnicalIndicator.objects.create(ticker=ticker, **tech_data)


@shared_task
def detect_market_regime():
    """Detect current market regime and store it."""
    result = detect_regime()
    from decimal import Decimal
    RegimeState.objects.create(
        regime=result["regime"],
        strategy_mode=result["strategy_mode"],
        vix=Decimal(str(result["vix"])) if result.get("vix") else None,
        treasury_10y=Decimal(str(result["treasury_10y"])) if result.get("treasury_10y") else None,
        yield_delta_30d=Decimal(str(result["yield_delta_30d"])) if result.get("yield_delta_30d") else None,
        yield_curve=Decimal(str(result["yield_curve"])) if result.get("yield_curve") else None,
        spy_trend=result.get("spy_trend", ""),
        score=Decimal(str(result["score"])),
        signals=result["signals"],
    )
    return result


@shared_task
def generate_day_trade_signals():
    """Generate confluence-based day trade signals."""
    tickers = Ticker.objects.filter(is_active=True)[:100]
    for ticker in tickers:
        try:
            generate_confluence_signal(ticker, "day_trade")
        except Exception:
            pass


@shared_task
def generate_medium_signals():
    tickers = Ticker.objects.filter(is_active=True)[:200]
    for ticker in tickers:
        try:
            generate_confluence_signal(ticker, "medium_turnaround")
        except Exception:
            pass


@shared_task
def generate_seasonal_signals():
    wl = Watchlist.objects.filter(is_active=True).first()
    if not wl:
        return
    for ticker in wl.tickers.all():
        try:
            generate_confluence_signal(ticker, "seasonal_swing")
        except Exception:
            pass


@shared_task
def recompute_industry_rotation():
    for ticker in Ticker.objects.filter(is_active=True):
        try:
            compute_seasonal_pattern(ticker)
        except Exception:
            pass


@shared_task
def refresh_seasonal_patterns():
    for ticker in Ticker.objects.filter(is_active=True):
        try:
            compute_seasonal_pattern(ticker)
        except Exception:
            pass