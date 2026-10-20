from data.models import OHLCV
import numpy as np


def detect_rsi_divergence(ticker):
    """Detect RSI divergence from price.
    Bullish divergence: price makes lower low, RSI makes higher low.
    Bearish divergence: price makes higher high, RSI makes lower high.

    Also returns trend-adjusted RSI interpretation.
    """
    daily_bars = list(OHLCV.objects.filter(ticker=ticker, interval="1d").order_by("-timestamp")[:60])

    if len(daily_bars) < 30:
        return {"signals": ["Insufficient data"], "score": 0, "divergence": "none"}

    daily_bars.reverse()
    closes = [float(b.close) for b in daily_bars]

    rsi_values = _compute_rsi_series(closes, 14)
    if not rsi_values or len(rsi_values) < 20:
        return {"signals": ["Insufficient RSI data"], "score": 0, "divergence": "none"}

    current_rsi = rsi_values[-1]
    trend = _determine_trend(closes)

    thresholds = _get_trend_adjusted_thresholds(trend)

    swings = _find_swings(closes, rsi_values)

    divergence = "none"
    score = 0
    signals = []

    if len(swings["price_highs"]) >= 2 and len(swings["rsi_highs"]) >= 2:
        if swings["price_highs"][-1] > swings["price_highs"][-2] and \
           swings["rsi_highs"][-1] < swings["rsi_highs"][-2]:
            divergence = "bearish"
            score -= 0.4
            signals.append("Bearish RSI divergence — price new high but RSI lower high = exhaustion")

    if len(swings["price_lows"]) >= 2 and len(swings["rsi_lows"]) >= 2:
        if swings["price_lows"][-1] < swings["price_lows"][-2] and \
           swings["rsi_lows"][-1] > swings["rsi_lows"][-2]:
            divergence = "bullish"
            score += 0.4
            signals.append("Bullish RSI divergence — price new low but RSI higher low = accumulation")

    if trend == "strong_uptrend":
        if current_rsi > thresholds["overbought"]:
            signals.append(f"RSI {current_rsi:.1f} in strong uptrend — strength signal, not automatic sell (threshold={thresholds['overbought']})")
            score += 0.05
        elif current_rsi < thresholds["oversold"]:
            signals.append(f"RSI {current_rsi:.1f} dipped in strong uptrend — potential buy the dip")
            score += 0.15
    elif trend == "strong_downtrend":
        if current_rsi < thresholds["oversold"]:
            signals.append(f"RSI {current_rsi:.1f} in strong downtrend — weakness, not automatic buy (threshold={thresholds['oversold']})")
            score -= 0.05
        elif current_rsi > thresholds["overbought"]:
            signals.append(f"RSI {current_rsi:.1f} bounced in strong downtrend — potential short the bounce")
            score -= 0.15
    else:
        if current_rsi < thresholds["oversold"]:
            score += 0.2
            signals.append(f"RSI {current_rsi:.1f} oversold in range — potential bounce")
        elif current_rsi > thresholds["overbought"]:
            score -= 0.2
            signals.append(f"RSI {current_rsi:.1f} overbought in range — potential pullback")
        else:
            signals.append(f"RSI {current_rsi:.1f} neutral in range market")

    return {
        "current_rsi": round(current_rsi, 2),
        "divergence": divergence,
        "trend": trend,
        "thresholds": thresholds,
        "signals": signals,
        "score": round(max(-1.0, min(1.0, score)), 4),
    }


def _compute_rsi_series(closes, period=14):
    """Compute RSI series from close prices."""
    if len(closes) < period + 1:
        return []

    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    rsi_values = []
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        rsi_values.append(rsi)

    return rsi_values


def _determine_trend(closes):
    """Determine trend strength from closes."""
    if len(closes) < 50:
        return "unknown"
    ema_20 = _ema(closes, 20)
    ema_50 = _ema(closes, 50)
    current = closes[-1]

    if current > ema_20 > ema_50:
        return "strong_uptrend"
    elif current < ema_20 < ema_50:
        return "strong_downtrend"
    else:
        return "range"


def _ema(values, period):
    """Compute EMA for a list of values."""
    if len(values) < period:
        return np.mean(values) if values else 0
    multiplier = 2 / (period + 1)
    ema = np.mean(values[:period])
    for i in range(period, len(values)):
        ema = (values[i] - ema) * multiplier + ema
    return ema


def _get_trend_adjusted_thresholds(trend):
    """In strong trends, shift RSI thresholds to 80/20."""
    if trend == "strong_uptrend" or trend == "strong_downtrend":
        return {"overbought": 80, "oversold": 20}
    return {"overbought": 70, "oversold": 30}


def _find_swings(closes, rsi_values):
    """Find swing highs/lows in price and corresponding RSI values."""
    price_highs = []
    rsi_highs = []
    price_lows = []
    rsi_lows = []

    window = 5
    for i in range(window, len(closes) - window):
        if closes[i] == max(closes[i - window:i + window + 1]):
            price_highs.append(closes[i])
            rsi_idx = i - 14
            if 0 <= rsi_idx < len(rsi_values):
                rsi_highs.append(rsi_values[rsi_idx])
        if closes[i] == min(closes[i - window:i + window + 1]):
            price_lows.append(closes[i])
            rsi_idx = i - 14
            if 0 <= rsi_idx < len(rsi_values):
                rsi_lows.append(rsi_values[rsi_idx])

    return {"price_highs": price_highs, "rsi_highs": rsi_highs, "price_lows": price_lows, "rsi_lows": rsi_lows}