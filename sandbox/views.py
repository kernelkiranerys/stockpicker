from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from sandbox.models import Portfolio, Position, Trade, EquityPoint


def sandbox_overview(request):
    portfolios = Portfolio.objects.all().order_by("name")
    return render(request, "sandbox/overview.html", {"portfolios": portfolios})


def sandbox_detail(request, portfolio_id):
    portfolio = get_object_or_404(Portfolio, id=portfolio_id)
    positions = portfolio.positions.select_related("ticker", "entry_signal").all()
    trades = portfolio.trades.select_related("ticker", "signal").order_by("-executed_at")[:50]
    closed_trades = portfolio.trades.filter(side="SELL", realized_pnl__isnull=False)
    total_trades = closed_trades.count()
    winning = closed_trades.filter(realized_pnl__gt=0).count()
    losing = closed_trades.filter(realized_pnl__lte=0).count()
    win_rate = (winning / total_trades * 100) if total_trades > 0 else 0
    total_realized = sum(float(t.realized_pnl or 0) for t in closed_trades)
    equity_points = portfolio.equity_points.order_by("timestamp").all()
    return render(request, "sandbox/detail.html", {
        "portfolio": portfolio,
        "positions": positions,
        "trades": trades,
        "win_rate": round(win_rate, 1),
        "total_trades": total_trades,
        "winning": winning,
        "losing": losing,
        "total_realized": round(total_realized, 2),
        "equity_points": list(equity_points),
    })


def sandbox_reset(request, portfolio_id):
    if request.method == "POST":
        portfolio = get_object_or_404(Portfolio, id=portfolio_id)
        portfolio.positions.all().delete()
        portfolio.trades.all().delete()
        portfolio.equity_points.all().delete()
        portfolio.cash = portfolio.starting_cash
        portfolio.is_active = True
        portfolio.save()
        messages.success(request, f"{portfolio.name} has been reset.")
    return redirect("sandbox:detail", portfolio_id=portfolio_id)


def equity_data(request, portfolio_id):
    portfolio = get_object_or_404(Portfolio, id=portfolio_id)
    points = portfolio.equity_points.order_by("timestamp").all()
    data = [
        {
            "timestamp": p.timestamp.isoformat(),
            "equity": float(p.total_equity),
            "benchmark": float(p.benchmark_equity or 0),
            "pnl_pct": float(p.portfolio_pnl_pct),
            "benchmark_pnl_pct": float(p.benchmark_pnl_pct),
        }
        for p in points
    ]
    return JsonResponse({"data": data})


def trades_data(request, portfolio_id):
    portfolio = get_object_or_404(Portfolio, id=portfolio_id)
    trades = portfolio.trades.select_related("ticker").order_by("-executed_at")[:50]
    data = [
        {
            "executed_at": t.executed_at.isoformat(),
            "ticker": t.ticker.symbol,
            "side": t.side,
            "quantity": float(t.quantity),
            "price": float(t.price),
            "realized_pnl": float(t.realized_pnl) if t.realized_pnl else None,
            "reason": t.reason,
        }
        for t in trades
    ]
    return JsonResponse({"data": data})