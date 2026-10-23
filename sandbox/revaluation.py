from decimal import Decimal
from django.utils import timezone as djtz

from sandbox.models import Portfolio, Position, EquityPoint
from tickers.models import Ticker
from data.models import OHLCV
from data.connectors.yfinance_connector import fetch_current_price


def revalue_positions():
    """Revalue all open positions at current prices for all active portfolios."""
    for portfolio in Portfolio.objects.filter(is_active=True):
        for position in portfolio.positions.all():
            try:
                price = fetch_current_price(position.ticker)
                if price:
                    position.current_price = price
                    position.save(update_fields=["current_price"])
            except Exception:
                pass


def record_equity_point():
    """Record an equity curve data point for all active portfolios."""
    for portfolio in Portfolio.objects.filter(is_active=True):
        positions_value = sum(
            float(p.quantity) * float(p.current_price or p.entry_price)
            for p in portfolio.positions.all()
        )
        total_equity = float(portfolio.cash) + positions_value
        pnl_pct = ((total_equity - float(portfolio.starting_cash)) / float(portfolio.starting_cash)) * 100 if float(portfolio.starting_cash) > 0 else 0

        benchmark_price = _get_benchmark_price()
        benchmark_equity = 0
        benchmark_pnl_pct = 0
        if benchmark_price:
            first_point = EquityPoint.objects.filter(portfolio=portfolio).order_by("timestamp").first()
            if first_point and first_point.benchmark_price:
                benchmark_equity = (float(portfolio.starting_cash) / float(first_point.benchmark_price)) * float(benchmark_price)
                benchmark_pnl_pct = ((benchmark_equity - float(portfolio.starting_cash)) / float(portfolio.starting_cash)) * 100
            else:
                benchmark_equity = float(portfolio.starting_cash)
                benchmark_pnl_pct = 0

        excess = pnl_pct - benchmark_pnl_pct

        EquityPoint.objects.create(
            portfolio=portfolio,
            cash=portfolio.cash,
            positions_value=Decimal(str(round(positions_value, 2))),
            total_equity=Decimal(str(round(total_equity, 2))),
            benchmark_price=Decimal(str(benchmark_price)) if benchmark_price else None,
            benchmark_equity=Decimal(str(round(benchmark_equity, 2))),
            portfolio_pnl_pct=Decimal(str(round(pnl_pct, 4))),
            benchmark_pnl_pct=Decimal(str(round(benchmark_pnl_pct, 4))),
            excess_return=Decimal(str(round(excess, 4))),
        )


def _get_benchmark_price():
    """Get current SPY price."""
    try:
        spy = Ticker.objects.get(symbol="SPY")
        price = fetch_current_price(spy)
        return float(price) if price else None
    except Ticker.DoesNotExist:
        return None
    except Exception:
        return None