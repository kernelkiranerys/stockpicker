from data.connectors.alpaca_connector import submit_market_order, get_positions, get_account, close_all_positions
from django.conf import settings


def execute_alpaca_trade(signal):
    """Execute a trade in Alpaca paper trading based on a signal.
    Only executes if conviction > threshold (default 75).
    """
    threshold = settings.CONVICTION_THRESHOLD
    conviction = round(float(signal.confidence) * 100) if signal.confidence else 0

    if conviction < threshold:
        return {"skipped": True, "reason": f"Conviction {conviction} < threshold {threshold}"}

    symbol = signal.ticker.symbol

    if signal.action == "BUY":
        result = submit_market_order(symbol, qty=1, side="buy")
        return result
    elif signal.action in ("SELL", "TRIM"):
        result = submit_market_order(symbol, qty=1, side="sell")
        return result

    return {"skipped": True, "reason": f"Action {signal.action} not executable"}


def sync_alpaca_positions(portfolio):
    """Sync local Position records with Alpaca paper trading positions."""
    positions = get_positions()
    if not positions:
        return 0

    from sandbox.models import Position
    from tickers.models import Ticker
    from decimal import Decimal
    from django.utils import timezone as djtz

    count = 0
    for pos_data in positions:
        try:
            ticker = Ticker.objects.get(symbol=pos_data["symbol"])
            pos, created = Position.objects.update_or_create(
                portfolio=portfolio,
                ticker=ticker,
                defaults={
                    "quantity": Decimal(str(pos_data["qty"])),
                    "entry_price": Decimal(str(pos_data["avg_entry_price"])),
                    "entry_date": djtz.now(),
                    "current_price": Decimal(str(pos_data["current_price"])),
                },
            )
            count += 1
        except Ticker.DoesNotExist:
            continue

    return count


def get_portfolio_value():
    """Get total portfolio value from Alpaca."""
    account = get_account()
    if account:
        return account.get("portfolio_value", 0)
    return 0