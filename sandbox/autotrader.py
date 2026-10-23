from decimal import Decimal
from datetime import timezone
from django.utils import timezone as djtz

from sandbox.models import Portfolio, Position, Trade
from signals.models import Signal


def execute_buy(portfolio, signal):
    """Execute a paper buy trade based on a BUY signal."""
    if signal.action not in (Signal.ACTION_BUY,):
        return None

    existing = Position.objects.filter(portfolio=portfolio, ticker=signal.ticker).first()
    if existing:
        return None

    available_cash = float(portfolio.cash)
    if available_cash <= 0:
        return None

    confidence = float(signal.confidence)
    if portfolio.position_sizing == Portfolio.SIZING_CONFIDENCE:
        position_size = available_cash * confidence
    elif portfolio.position_sizing == Portfolio.SIZING_EQUAL:
        position_size = available_cash * 0.10
    else:
        position_size = available_cash * 0.10

    if position_size < 1:
        return None

    price = float(signal.entry_price) if signal.entry_price else 0
    if price <= 0:
        if signal.ticker.last_price:
            price = float(signal.ticker.last_price)
        else:
            return None

    fees = float(portfolio.fees_per_trade)
    quantity = Decimal(str(round((position_size - fees) / price, 6)))
    if quantity <= 0:
        return None

    total_cost = Decimal(str(price)) * quantity + Decimal(str(fees))
    if total_cost > portfolio.cash:
        quantity = Decimal(str(round(float(portfolio.cash - Decimal(str(fees))) / price, 6)))
        total_cost = Decimal(str(price)) * quantity + Decimal(str(fees))
        if quantity <= 0:
            return None

    position = Position.objects.create(
        portfolio=portfolio,
        ticker=signal.ticker,
        quantity=quantity,
        entry_price=Decimal(str(price)),
        entry_date=djtz.now(),
        entry_signal=signal,
        entry_confidence=signal.confidence,
        current_price=Decimal(str(price)),
        signal_source=signal.signal_type,
    )

    portfolio.cash -= total_cost
    portfolio.save(update_fields=["cash"])

    trade = Trade.objects.create(
        portfolio=portfolio,
        ticker=signal.ticker,
        side=Trade.SIDE_BUY,
        quantity=quantity,
        price=Decimal(str(price)),
        signal=signal,
        fees=Decimal(str(fees)),
        reason=signal.reasoning[:500],
        signal_source=signal.signal_type,
    )

    return trade


def execute_sell(portfolio, signal):
    """Execute a paper sell trade based on a SELL/TRIM signal."""
    if signal.action not in (Signal.ACTION_SELL, Signal.ACTION_TRIM):
        return None

    position = Position.objects.filter(portfolio=portfolio, ticker=signal.ticker).first()
    if not position:
        return None

    price = float(signal.entry_price) if signal.entry_price else 0
    if price <= 0:
        if signal.ticker.last_price:
            price = float(signal.ticker.last_price)
        elif position.current_price:
            price = float(position.current_price)
        else:
            return None

    if signal.action == Signal.ACTION_TRIM:
        sell_quantity = position.quantity / 2
    else:
        sell_quantity = position.quantity

    proceeds = Decimal(str(price)) * sell_quantity
    fees = Decimal(str(portfolio.fees_per_trade))
    portfolio.cash += proceeds - fees
    portfolio.save(update_fields=["cash"])

    realized_pnl = (Decimal(str(price)) - position.entry_price) * sell_quantity
    entry_total = position.entry_price * sell_quantity
    realized_pnl_pct = (float(realized_pnl) / float(entry_total) * 100) if float(entry_total) > 0 else 0

    trade = Trade.objects.create(
        portfolio=portfolio,
        ticker=signal.ticker,
        side=Trade.SIDE_SELL,
        quantity=sell_quantity,
        price=Decimal(str(price)),
        signal=signal,
        realized_pnl=realized_pnl,
        realized_pnl_pct=Decimal(str(round(realized_pnl_pct, 4))),
        fees=fees,
        reason=signal.reasoning[:500],
        signal_source=signal.signal_type,
    )

    position.quantity -= sell_quantity
    if position.quantity <= 0:
        position.delete()
    else:
        position.save(update_fields=["quantity"])

    return trade