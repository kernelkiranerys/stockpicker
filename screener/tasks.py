from celery import shared_task
from tickers.models import Ticker, Watchlist
from screener.models import ScreenedUniverse
from screener.stage1_fundamentals import run_fundamental_screen
from screener.stage2_liquidity import run_liquidity_volatility_filter
from screener.stage3_correlation import run_historical_correlation
from screener.stage4_regime import run_regime_detection
from screener.stage5_conviction import run_conviction_scoring
from screener.stage6_news import run_news_overlay
from django.utils import timezone as djtz


@shared_task
def run_weekly_fundamental_screen():
    """Weekly: Stage 1 — fundamental screen of the full universe."""
    return run_fundamental_screen()


@shared_task
def run_daily_screening_pipeline():
    """Daily pre-market: Run the full screening pipeline.
    Stage 1 → 2 → 3 → 4 → 5 → 6

    Narrows from ~200 tickers to high-conviction candidates.
    """
    print("=== Daily Screening Pipeline ===")

    print("Stage 1: Fundamental screen...")
    stage1_pass = run_fundamental_screen()
    print(f"  Passed: {len(stage1_pass)} tickers")

    print("Stage 2: Liquidity/volatility filter...")
    stage2_pass = run_liquidity_volatility_filter(stage1_pass)
    print(f"  Passed: {len(stage2_pass)} tickers")

    print("Stage 3: Historical signal correlation...")
    stage3_pass = run_historical_correlation(stage2_pass)
    print(f"  Passed: {len(stage3_pass)} tickers")

    print("Stage 4: Regime detection...")
    regime = run_regime_detection()
    print(f"  Regime: {regime['regime']} — strategy: {regime['strategy_mode']}")

    print("Stage 5: AI conviction scoring...")
    high_conviction = run_conviction_scoring(stage3_pass)
    print(f"  High conviction (>threshold): {len(high_conviction)} tickers")

    print("Stage 6: News overlay...")
    final_candidates = run_news_overlay([t for t, _ in high_conviction])
    print(f"  Final candidates: {len(final_candidates)} tickers")

    return {
        "stage1": len(stage1_pass),
        "stage2": len(stage2_pass),
        "stage3": len(stage3_pass),
        "regime": regime["regime"],
        "high_conviction": len(high_conviction),
        "final": len(final_candidates),
    }


@shared_task
def run_regime_check():
    """Standalone regime detection task."""
    return run_regime_detection()