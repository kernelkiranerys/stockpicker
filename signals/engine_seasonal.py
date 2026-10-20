from data.models import OHLCV
from decimal import Decimal
from collections import defaultdict
import statistics


def compute_seasonal_pattern(ticker, years=5):
    """Compute average monthly returns for a ticker over the past N years.
    Returns dict: month (1-12) → average return %.
    """
    ohlcv = OHLCV.objects.filter(ticker=ticker, interval="1d").order_by("timestamp")

    if not ohlcv.exists():
        return {}

    monthly_returns = defaultdict(list)
    prev_close = None
    prev_month = None

    for bar in ohlcv:
        month = bar.timestamp.month
        close = float(bar.close)
        if prev_close is not None and prev_month is not None:
            if month != prev_month:
                ret = (close - prev_close) / prev_close * 100
                monthly_returns[prev_month].append(ret)
                prev_close = close
        else:
            prev_close = close
        prev_month = month

    if prev_month is not None:
        last_bar = list(ohlcv)[-1]
        if prev_close and float(last_bar.close) != prev_close:
            pass

    seasonal = {}
    for month in range(1, 13):
        if month in monthly_returns and monthly_returns[month]:
            avg = statistics.mean(monthly_returns[month])
            seasonal[month] = round(avg, 2)

    return seasonal


def score_seasonal(ticker):
    """Score current seasonal pattern for a ticker.
    Returns dict with score (-1 to 1) and signals.
    """
    from datetime import datetime
    seasonal = compute_seasonal_pattern(ticker)
    if not seasonal:
        return {"score": 0, "signals": [], "seasonal_pattern": {}}

    current_month = datetime.now().month
    current_avg = seasonal.get(current_month, 0)

    signals = []
    score = 0

    if current_avg > 3:
        score = 0.6
        signals.append(f"Strong seasonal pattern for month {current_month} (+{current_avg}% avg)")
    elif current_avg > 1:
        score = 0.3
        signals.append(f"Positive seasonal pattern for month {current_month} (+{current_avg}% avg)")
    elif current_avg < -3:
        score = -0.6
        signals.append(f"Strong negative seasonal for month {current_month} ({current_avg}% avg)")
    elif current_avg < -1:
        score = -0.3
        signals.append(f"Negative seasonal pattern for month {current_month} ({current_avg}% avg)")
    else:
        signals.append(f"Neutral seasonal pattern for month {current_month} ({current_avg}% avg)")

    return {
        "score": round(score, 4),
        "signals": signals,
        "seasonal_pattern": seasonal,
        "current_month_avg": current_avg,
    }