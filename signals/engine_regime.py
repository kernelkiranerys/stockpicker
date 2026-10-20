from data.models import MacroIndicator, OHLCV
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone as djtz


def detect_regime():
    """Detect current market regime.
    Returns dict with regime type, VIX level, Treasury yield delta, strategy mode.

    Regimes:
    - trending_bull: Favor breakout strategies, high-beta stocks
    - trending_bear: Favor defensive, reduce positions
    - range_bound: Favor mean-reversion strategies
    - high_volatility: Reduce position sizes, favor mean reversion
    - low_volatility: Increase position sizes, favor momentum
    """
    vix = _get_macro_value("VIXCLS")
    treasury_10y = _get_macro_value("DGS10")
    treasury_2y = _get_macro_value("DGS2")

    yield_delta_30d = _compute_yield_delta("DGS10", 30)
    yield_curve = _compute_yield_curve(treasury_10y, treasury_2y)

    signals = []
    regime = "unknown"
    strategy_mode = "neutral"

    if vix is not None:
        if vix > 30:
            regime = "high_volatility"
            strategy_mode = "mean_reversion"
            signals.append(f"VIX={vix:.1f} — high volatility regime, reduce position sizes, favor mean reversion")
        elif vix < 15:
            regime = "low_volatility"
            strategy_mode = "momentum"
            signals.append(f"VIX={vix:.1f} — low volatility regime, increase position sizes, favor momentum")
        else:
            signals.append(f"VIX={vix:.1f} — normal volatility")

    if yield_delta_30d is not None:
        if yield_delta_30d > 50:
            signals.append(f"10Y yield rose {yield_delta_30d:.0f}bps in 30 days — yield shock, reduce long equity conviction")
            if regime == "unknown":
                regime = "yield_shock"
                strategy_mode = "defensive"
        elif yield_delta_30d < -50:
            signals.append(f"10Y yield fell {abs(yield_delta_30d):.0f}bps in 30 days — bullish for equities")
            if regime in ("unknown", "low_volatility"):
                regime = "trending_bull"
                strategy_mode = "breakout"

    if yield_curve is not None:
        if yield_curve < -50:
            signals.append(f"Yield curve inverted ({yield_curve:.0f}bps) — recession risk, defensive bias")
        elif yield_curve > 50:
            signals.append(f"Yield curve steep ({yield_curve:.0f}bps) — growth expectations positive")

    spy_trend = _detect_spy_trend()
    if spy_trend:
        signals.append(f"SPY trend: {spy_trend}")
        if spy_trend == "uptrend" and regime in ("unknown", "low_volatility"):
            regime = "trending_bull"
            strategy_mode = "breakout"
        elif spy_trend == "downtrend":
            regime = "trending_bear"
            strategy_mode = "defensive"
        elif spy_trend == "range":
            if regime in ("unknown", "low_volatility"):
                regime = "range_bound"
                strategy_mode = "mean_reversion"

    score = _regime_to_score(regime)

    return {
        "regime": regime,
        "strategy_mode": strategy_mode,
        "vix": vix,
        "treasury_10y": treasury_10y,
        "treasury_2y": treasury_2y,
        "yield_delta_30d": yield_delta_30d,
        "yield_curve": yield_curve,
        "spy_trend": spy_trend,
        "signals": signals,
        "score": score,
    }


def _get_macro_value(name):
    """Get latest macro indicator value."""
    try:
        indicator = MacroIndicator.objects.filter(name=name).order_by("-date").first()
        if indicator and indicator.value is not None:
            return float(indicator.value)
    except Exception:
        pass
    return None


def _compute_yield_delta(series_id, days):
    """Compute change in yield over N days (in basis points)."""
    try:
        cutoff = djtz.now().date() - timedelta(days=days)
        recent = MacroIndicator.objects.filter(
            name=series_id, date__gte=cutoff
        ).order_by("date")
        if recent.count() >= 2:
            latest = float(recent.last().value)
            oldest = float(recent.first().value)
            return round((latest - oldest) * 100, 1)
    except Exception:
        pass
    return None


def _compute_yield_curve(treasury_10y, treasury_2y):
    """Compute yield curve spread (10Y - 2Y) in basis points."""
    if treasury_10y is not None and treasury_2y is not None:
        return round((treasury_10y - treasury_2y) * 100, 1)
    return None


def _detect_spy_trend():
    """Determine SPY trend from OHLCV data."""
    try:
        from tickers.models import Ticker
        spy = Ticker.objects.get(symbol="SPY")
        bars = OHLCV.objects.filter(ticker=spy, interval="1d").order_by("-timestamp")[:60]
        if bars.count() < 50:
            return None
        closes = [float(b.close) for b in reversed(list(bars))]
        ema_20 = _ema(closes, 20)
        ema_50 = _ema(closes, 50)
        current = closes[-1]
        if current > ema_20 > ema_50:
            return "uptrend"
        elif current < ema_20 < ema_50:
            return "downtrend"
        else:
            return "range"
    except Exception:
        return None


def _ema(values, period):
    if len(values) < period:
        return sum(values) / len(values) if values else 0
    multiplier = 2 / (period + 1)
    ema = sum(values[:period]) / period
    for i in range(period, len(values)):
        ema = (values[i] - ema) * multiplier + ema
    return ema


def _regime_to_score(regime):
    """Convert regime to a sentiment score."""
    scores = {
        "trending_bull": 0.5,
        "trending_bear": -0.5,
        "range_bound": 0.0,
        "high_volatility": -0.3,
        "low_volatility": 0.2,
        "yield_shock": -0.3,
        "unknown": 0.0,
    }
    return scores.get(regime, 0.0)