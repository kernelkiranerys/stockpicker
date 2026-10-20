from celery import shared_task
from datetime import timedelta
from django.utils import timezone as djtz
from signals.models import Signal
from signallog.models import SignalLogEntry
from data.models import OHLCV


@shared_task
def record_signal_outcomes():
    """Check historical signals and record whether they were correct.
    A signal is 'win' if the price moved in the predicted direction
    within 14 days of the signal.
    """
    cutoff = djtz.now() - timedelta(days=14)
    old_signals = Signal.objects.filter(
        created_at__lte=cutoff,
        log_entries__isnull=True,
    ).select_related("ticker")

    for signal in old_signals:
        entry_price = float(signal.entry_price) if signal.entry_price else 0
        if entry_price <= 0:
            continue

        signal_date = signal.created_at
        end_date = signal_date + timedelta(days=14)

        ohlcv_after = OHLCV.objects.filter(
            ticker=signal.ticker,
            interval="1d",
            timestamp__gte=signal_date,
            timestamp__lte=end_date,
        ).order_by("timestamp")

        if not ohlcv_after.exists():
            continue

        exit_price = float(ohlcv_after.last().close)
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        days = (ohlcv_after.last().timestamp - signal_date).days

        if signal.action == Signal.ACTION_BUY:
            outcome = "win" if pnl_pct > 0 else "loss"
        elif signal.action == Signal.ACTION_SELL:
            outcome = "win" if pnl_pct < 0 else "loss"
        elif signal.action == Signal.ACTION_TRIM:
            outcome = "win" if pnl_pct < 0 else "loss"
        else:
            outcome = "pending"

        SignalLogEntry.objects.create(
            signal=signal,
            outcome=outcome,
            pnl_pct=round(pnl_pct, 4),
            days_to_outcome=days,
            entry_price=signal.entry_price,
            exit_price=ohlcv_after.last().close,
        )