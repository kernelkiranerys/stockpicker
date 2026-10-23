from decimal import Decimal
from sandbox.models import Portfolio, Trade, EquityPoint
import math


def compute_performance(portfolio):
    """Compute comprehensive performance analytics for a portfolio."""
    trades = Trade.objects.filter(portfolio=portfolio, side="SELL", realized_pnl__isnull=False)

    total_trades = trades.count()
    wins = trades.filter(realized_pnl__gt=0)
    losses = trades.filter(realized_pnl__lte=0)
    win_count = wins.count()
    loss_count = losses.count()
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0

    avg_win = _avg([float(t.realized_pnl) for t in wins]) if win_count > 0 else 0
    avg_loss = _avg([float(t.realized_pnl) for t in losses]) if loss_count > 0 else 0

    equity_points = list(EquityPoint.objects.filter(portfolio=portfolio).order_by("timestamp"))
    max_drawdown = _max_drawdown([float(p.total_equity) for p in equity_points])
    sharpe = _sharpe_ratio([float(p.portfolio_pnl_pct) for p in equity_points])

    best_trade = trades.order_by("-realized_pnl").first()
    worst_trade = trades.order_by("realized_pnl").first()

    by_source = _win_rate_by_source(trades)

    avg_hold_days = _avg_hold_days(portfolio)

    return {
        "win_rate": round(win_rate, 1),
        "total_trades": total_trades,
        "win_count": win_count,
        "loss_count": loss_count,
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "max_drawdown": round(max_drawdown, 2),
        "sharpe": round(sharpe, 2),
        "best_trade": {
            "ticker": best_trade.ticker.symbol,
            "pnl": float(best_trade.realized_pnl),
        } if best_trade else None,
        "worst_trade": {
            "ticker": worst_trade.ticker.symbol,
            "pnl": float(worst_trade.realized_pnl),
        } if worst_trade else None,
        "by_source": by_source,
        "avg_hold_days": round(avg_hold_days, 1),
    }


def _avg(values):
    return sum(values) / len(values) if values else 0


def _max_drawdown(equity_curve):
    if not equity_curve or len(equity_curve) < 2:
        return 0
    peak = equity_curve[0]
    max_dd = 0
    for value in equity_curve:
        if value > peak:
            peak = value
        dd = (peak - value) / peak * 100 if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd
    return max_dd


def _sharpe_ratio(returns):
    if not returns or len(returns) < 2:
        return 0
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    std = math.sqrt(variance)
    if std == 0:
        return 0
    return mean / std


def _win_rate_by_source(trades):
    sources = {}
    for trade in trades:
        src = trade.signal_source or "unknown"
        if src not in sources:
            sources[src] = {"wins": 0, "losses": 0, "total": 0}
        sources[src]["total"] += 1
        if float(trade.realized_pnl or 0) > 0:
            sources[src]["wins"] += 1
        else:
            sources[src]["losses"] += 1
    for src, data in sources.items():
        data["win_rate"] = round(data["wins"] / data["total"] * 100, 1) if data["total"] > 0 else 0
    return sources


def _avg_hold_days(portfolio):
    from sandbox.models import Position
    positions = Position.objects.filter(portfolio=portfolio).all()
    if not positions:
        return 0
    total_days = 0
    count = 0
    for pos in positions:
        if pos.entry_date:
            delta = djtz_now() - pos.entry_date
            total_days += delta.days
            count += 1
    return total_days / count if count > 0 else 0


def djtz_now():
    from django.utils import timezone
    return timezone.now()