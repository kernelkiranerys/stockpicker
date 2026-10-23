from celery import shared_task
from sandbox.autotrader import execute_buy, execute_sell
from sandbox.alpaca_autotrader import execute_alpaca_trade, sync_alpaca_positions, get_portfolio_value
from sandbox.revaluation import revalue_positions, record_equity_point
from sandbox.models import Portfolio
from signals.models import Signal


@shared_task
def execute_signal_trade(signal_id):
    """Called when a signal is emitted. Auto-executes on matching portfolios."""
    signal = Signal.objects.get(id=signal_id)
    portfolios = Portfolio.objects.filter(signal_mode=signal.signal_type, is_active=True)

    for portfolio in portfolios:
        try:
            if signal.action == Signal.ACTION_BUY:
                execute_buy(portfolio, signal)
            elif signal.action in (Signal.ACTION_SELL, Signal.ACTION_TRIM):
                execute_sell(portfolio, signal)
        except Exception as e:
            print(f"AutoTrader error for {portfolio.name}: {e}")

    try:
        alpaca_result = execute_alpaca_trade(signal)
        print(f"Alpaca: {alpaca_result}")
    except Exception as e:
        print(f"Alpaca error: {e}")


@shared_task
def sync_alpaca_positions_task():
    """Sync Alpaca positions to local DB."""
    for portfolio in Portfolio.objects.filter(is_active=True):
        try:
            count = sync_alpaca_positions(portfolio)
            print(f"Synced {count} positions for {portfolio.name}")
        except Exception as e:
            print(f"Alpaca sync error for {portfolio.name}: {e}")


@shared_task
def revalue_positions_task():
    revalue_positions()


@shared_task
def record_equity_point_task():
    record_equity_point()