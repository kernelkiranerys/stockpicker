from data.connectors.yfinance_connector import fetch_option_chain
from decimal import Decimal


def detect_unusual_activity(ticker):
    """Check options chain for unusual activity patterns.
    Returns dict with scores and flags.
    """
    chain = fetch_option_chain(ticker)
    if not chain:
        return {"score": 0, "signals": [], "unusual": False}

    signals = []
    score = 0

    vol_oi = float(chain.get("vol_oi_ratio") or 0)
    pcr = float(chain.get("put_call_ratio") or 0)
    iv = float(chain.get("implied_volatility") or 0)
    unusual = chain.get("unusual_activity", False)

    if unusual:
        score += 0.5
        signals.append(f"Unusual options activity detected (vol/OI={vol_oi:.2f})")

    if vol_oi > 2.0:
        score += 0.3
        signals.append(f"High volume vs open interest ({vol_oi:.2f})")
    elif vol_oi > 1.0:
        score += 0.1
        signals.append(f"Elevated volume vs open interest ({vol_oi:.2f})")

    if pcr > 1.5:
        score -= 0.2
        signals.append(f"Bearish put/call ratio ({pcr:.2f})")
    elif pcr < 0.5:
        score += 0.2
        signals.append(f"Bullish put/call ratio ({pcr:.2f})")

    if iv > 1.0:
        score += 0.1
        signals.append(f"High implied volatility ({iv:.2f})")

    score = max(-1.0, min(1.0, score))

    return {
        "score": round(score, 4),
        "signals": signals,
        "unusual": unusual,
        "vol_oi_ratio": vol_oi,
        "put_call_ratio": pcr,
        "iv": iv,
    }