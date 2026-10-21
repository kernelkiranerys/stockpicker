from tickers.models import Ticker, Sector
from data.models import Fundamental, OHLCV
from screener.models import ScreenedUniverse
from decimal import Decimal
from datetime import date
from django.utils import timezone as djtz


def run_fundamental_screen(min_market_cap=2e9, min_eps=0):
    """Stage 1: Filter by fundamental criteria.
    - Market cap > $2B (exclude micro-caps)
    - Positive EPS (profitable companies)
    - Specific sectors for seasonal/mean-reversion strategies

    Returns list of tickers that pass.
    """
    today = djtz.now().date()
    passing = []

    for ticker in Ticker.objects.filter(is_active=True):
        fund = Fundamental.objects.filter(ticker=ticker).order_by("-date").first()
        if not fund:
            continue

        market_cap = float(fund.market_cap) if fund.market_cap else 0
        pe_ratio = float(fund.pe_ratio) if fund.pe_ratio else None

        passes = True
        notes = []

        if market_cap < min_market_cap:
            passes = False
            notes.append(f"Market cap ${market_cap/1e9:.1f}B < ${min_market_cap/1e9:.1f}B")

        if min_eps > 0 and fund.earnings_growth is not None:
            if float(fund.earnings_growth) < 0:
                notes.append("Negative earnings growth")

        sector_name = ticker.sector.name if ticker.sector else "Unknown"
        if ticker.sector:
            preferred = ["Energy", "Materials", "Industrials", "Consumer Discretionary", "Technology"]
            if sector_name not in preferred:
                notes.append(f"Sector {sector_name} not in preferred list")

        result, _ = ScreenedUniverse.objects.get_or_create(
            ticker=ticker,
            screen_date=today,
            defaults={
                "market_cap": fund.market_cap,
                "eps": fund.earnings_growth,
                "pe_ratio": fund.pe_ratio,
                "passes_fundamental": passes,
                "notes": "; ".join(notes),
                "raw": {"market_cap": market_cap, "pe_ratio": pe_ratio},
            },
        )

        if passes:
            passing.append(ticker)

    return passing