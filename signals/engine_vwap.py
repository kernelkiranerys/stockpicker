from data.connectors.yfinance_connector import fetch_intraday_bars, compute_vwap, compute_anchored_vwap


def analyze_vwap(ticker):
    """Full VWAP analysis for a ticker.
    Returns dict with current price, vwap, position, slope, signals.
    """
    bars = fetch_intraday_bars(ticker, interval="1m", period="1d")
    if not bars or len(bars) < 5:
        return {"vwap": 0, "signals": [], "position": "unknown", "score": 0}

    vwap, bars_with_vwap = compute_vwap(bars)
    current_price = bars[-1]["close"]
    position = "above" if current_price > vwap else "below"
    distance_pct = ((current_price - vwap) / vwap * 100) if vwap > 0 else 0

    slope = _compute_vwap_slope(bars_with_vwap[-20:]) if len(bars_with_vwap) >= 20 else 0

    signals = []
    score = 0

    if position == "above" and distance_pct > 0.3:
        score += 0.3
        signals.append(f"Price above VWAP (+{distance_pct:.2f}%) — bullish intraday")
    elif position == "below" and distance_pct < -0.3:
        score -= 0.3
        signals.append(f"Price below VWAP ({distance_pct:.2f}%) — bearish intraday")

    if slope > 0.001:
        score += 0.2
        signals.append("VWAP slope rising — bullish momentum")
    elif slope < -0.001:
        score -= 0.2
        signals.append("VWAP slope falling — bearish momentum")

    pullback_signal = _detect_vwap_pullback(bars_with_vwap, vwap)
    if pullback_signal:
        score += 0.15
        signals.append(f"VWAP pullback/rejection — {pullback_signal}")

    divergence = _detect_vwap_divergence(bars_with_vwap)
    if divergence:
        score -= 0.2
        signals.append(f"VWAP divergence — {divergence}")

    score = max(-1.0, min(1.0, score))

    return {
        "vwap": round(vwap, 6),
        "current_price": current_price,
        "position": position,
        "distance_pct": round(distance_pct, 4),
        "slope": round(slope, 6),
        "signals": signals,
        "score": round(score, 4),
        "bars": bars_with_vwap[-50:],
    }


def _compute_vwap_slope(recent_bars):
    """Compute the slope of VWAP over recent bars."""
    if len(recent_bars) < 2:
        return 0
    vwap_values = [b["vwap"] for b in recent_bars]
    n = len(vwap_values)
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(vwap_values) / n
    numerator = sum((x[i] - x_mean) * (vwap_values[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
    return numerator / denominator if denominator > 0 else 0


def _detect_vwap_pullback(bars, vwap):
    """Detect price pulling back to VWAP and bouncing or rejecting."""
    if len(bars) < 5:
        return None
    recent = bars[-5:]
    first = recent[0]
    last = recent[-1]
    if first["close"] < vwap and last["close"] > vwap:
        return "bounce off VWAP from below (bullish)"
    if first["close"] > vwap and last["close"] < vwap:
        return "rejection at VWAP from above (bearish)"
    return None


def _detect_vwap_divergence(bars):
    """Detect price making new high while VWAP makes lower high."""
    if len(bars) < 10:
        return None
    first_half = bars[:len(bars) // 2]
    second_half = bars[len(bars) // 2:]
    price_high_1 = max(b["close"] for b in first_half)
    price_high_2 = max(b["close"] for b in second_half)
    vwap_high_1 = max(b["vwap"] for b in first_half)
    vwap_high_2 = max(b["vwap"] for b in second_half)
    if price_high_2 > price_high_1 and vwap_high_2 < vwap_high_1:
        return "price new high, VWAP lower high — weakening momentum"
    return None