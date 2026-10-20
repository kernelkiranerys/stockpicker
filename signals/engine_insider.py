from data.models import InsiderTrade
from decimal import Decimal


def score_insider_flow(ticker):
    """Score insider trading activity for a ticker.
    Positive score = net buying (bullish), negative = net selling (bearish).
    Returns dict with score and signals list.
    """
    trades = InsiderTrade.objects.filter(ticker=ticker).order_by("-filing_date")[:20]

    if not trades:
        return {"score": 0, "signals": [], "net_shares": 0}

    net_shares = Decimal("0")
    buy_count = 0
    sell_count = 0

    for trade in trades:
        tx_type = (trade.transaction_type or "").upper()
        shares = trade.shares or Decimal("0")
        if "BUY" in tx_type or "PURCHASE" in tx_type or "A" in tx_type:
            net_shares += shares
            buy_count += 1
        elif "SELL" in tx_type or "SALE" in tx_type or "D" in tx_type:
            net_shares -= shares
            sell_count += 1

    signals = []
    score = 0

    if net_shares > 0:
        score = min(1.0, float(net_shares) / 100000)
        signals.append(f"Net insider buying ({net_shares} shares, {buy_count} buys vs {sell_count} sells)")
    elif net_shares < 0:
        score = max(-1.0, float(net_shares) / 100000)
        signals.append(f"Net insider selling ({net_shares} shares, {buy_count} buys vs {sell_count} sells)")
    else:
        signals.append("No significant insider activity")

    if buy_count > 3:
        score = min(1.0, score + 0.1)
        signals.append(f"Multiple insider buyers ({buy_count})")

    return {
        "score": round(score, 4),
        "signals": signals,
        "net_shares": float(net_shares),
        "buy_count": buy_count,
        "sell_count": sell_count,
    }