from data.models import OHLCV
from decimal import Decimal


def compute_rvol(ticker):
    """Compute Relative Volume (RVOL) for a ticker.
    RVOL = current volume / 20-day average volume.
    >2.0 = unusual interest, breakout likely to sustain.
    """
    daily_bars = OHLCV.objects.filter(ticker=ticker, interval="1d").order_by("-timestamp")[:21]

    if not daily_bars.exists() or daily_bars.count() < 2:
        return {"rvol": 0, "signals": [], "score": 0}

    bars = list(daily_bars)
    current_volume = int(bars[0].volume)

    avg_bars = bars[1:21]
    if not avg_bars:
        return {"rvol": 0, "signals": [], "score": 0}

    avg_volume = sum(int(b.volume) for b in avg_bars) / len(avg_bars)
    if avg_volume == 0:
        return {"rvol": 0, "signals": ["No volume data"], "score": 0}

    rvol = current_volume / avg_volume

    signals = []
    score = 0

    if rvol > 3.0:
        score += 0.4
        signals.append(f"Extreme RVOL ({rvol:.2f}x) — massive interest, breakout highly likely to sustain")
    elif rvol > 2.0:
        score += 0.3
        signals.append(f"High RVOL ({rvol:.2f}x) — unusual interest, breakout likely to sustain")
    elif rvol > 1.5:
        score += 0.1
        signals.append(f"Elevated RVOL ({rvol:.2f}x) — above normal interest")
    elif rvol < 0.5:
        score -= 0.1
        signals.append(f"Low RVOL ({rvol:.2f}x) — below normal interest, moves may not stick")
    else:
        signals.append(f"Normal RVOL ({rvol:.2f}x)")

    volume_trend = _volume_trend(avg_bars)
    if volume_trend == "rising":
        signals.append("Volume trend rising over 20 days")
        score += 0.05
    elif volume_trend == "falling":
        signals.append("Volume trend falling over 20 days")

    return {
        "rvol": round(rvol, 4),
        "current_volume": current_volume,
        "avg_volume": round(avg_volume, 2),
        "volume_trend": volume_trend,
        "signals": signals,
        "score": round(score, 4),
    }


def _volume_trend(bars):
    """Determine if volume is trending up or down."""
    if len(bars) < 10:
        return "unknown"
    first_half = bars[len(bars) // 2:]
    second_half = bars[:len(bars) // 2]
    avg_1 = sum(int(b.volume) for b in first_half) / len(first_half) if first_half else 0
    avg_2 = sum(int(b.volume) for b in second_half) / len(second_half) if second_half else 0
    if avg_2 > avg_1 * 1.1:
        return "rising"
    elif avg_2 < avg_1 * 0.9:
        return "falling"
    return "stable"