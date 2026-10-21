from decimal import Decimal
from datetime import datetime, date
from backtest.models import BacktestRun, BacktestTrade
from tickers.models import Ticker
from data.models import OHLCV
from signals.models import Signal
import math


def run_backtest(name, strategy, tickers, start_date, end_date, initial_capital=10000, slippage=0.001, commission=0.001):
    """Run a backtest using pre-computed signals (Approach A from the document).
    Point-in-time: signals only see data up to their creation date.
    """
    run = BacktestRun.objects.create(
        name=name,
        strategy=strategy,
        start_date=start_date,
        end_date=end_date,
        initial_capital=Decimal(str(initial_capital)),
        slippage_pct=Decimal(str(slippage * 100)),
        commission_pct=Decimal(str(commission * 100)),
        status="running",
    )

    try:
        capital = float(initial_capital)
        positions = {}
        trades = []

        signals = Signal.objects.filter(
            ticker__in=tickers,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
            signal_type=strategy if strategy != "confluence" else None,
        ).order_by("created_at") if strategy != "confluence" else Signal.objects.filter(
            ticker__in=tickers,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        ).order_by("created_at")

        for signal in signals:
            ticker = signal.ticker
            entry_price = float(signal.entry_price) if signal.entry_price else 0
            if entry_price <= 0:
                continue

            entry_price *= (1 + slippage)
            commission_cost = entry_price * commission

            if signal.action == "BUY" and ticker.symbol not in positions and capital > entry_price + commission_cost:
                qty = (capital * 0.1) / (entry_price + commission_cost)
                capital -= qty * (entry_price + commission_cost)
                positions[ticker.symbol] = {
                    "ticker": ticker,
                    "entry_date": signal.created_at.date(),
                    "entry_price": entry_price,
                    "quantity": qty,
                    "reasoning": signal.reasoning[:200],
                }

            elif signal.action in ("SELL", "TRIM") and ticker.symbol in positions:
                pos = positions[ticker.symbol]
                exit_price = entry_price * (1 - slippage)
                qty = pos["quantity"]
                pnl = (exit_price - pos["entry_price"]) * qty - exit_price * qty * commission
                pnl_pct = (exit_price - pos["entry_price"]) / pos["entry_price"] * 100
                capital += qty * (exit_price - exit_price * qty * commission)

                trades.append({
                    "ticker": ticker,
                    "side": "SELL",
                    "entry_date": pos["entry_date"],
                    "entry_price": Decimal(str(round(pos["entry_price"], 6))),
                    "exit_date": signal.created_at.date(),
                    "exit_price": Decimal(str(round(exit_price, 6))),
                    "quantity": Decimal(str(round(qty, 6))),
                    "pnl": Decimal(str(round(pnl, 2))),
                    "pnl_pct": Decimal(str(round(pnl_pct, 4))),
                    "signal_reasoning": signal.reasoning[:500],
                })
                del positions[ticker.symbol]

        for symbol, pos in positions.items():
            latest_bar = OHLCV.objects.filter(
                ticker=pos["ticker"], interval="1d",
                timestamp__date__lte=end_date,
            ).order_by("-timestamp").first()
            if latest_bar:
                exit_price = float(latest_bar.close)
                pnl = (exit_price - pos["entry_price"]) * pos["quantity"]
                pnl_pct = (exit_price - pos["entry_price"]) / pos["entry_price"] * 100
                capital += pos["quantity"] * exit_price
                trades.append({
                    "ticker": pos["ticker"],
                    "side": "SELL",
                    "entry_date": pos["entry_date"],
                    "entry_price": Decimal(str(round(pos["entry_price"], 6))),
                    "exit_date": end_date,
                    "exit_price": Decimal(str(round(exit_price, 6))),
                    "quantity": Decimal(str(round(pos["quantity"], 6))),
                    "pnl": Decimal(str(round(pnl, 2))),
                    "pnl_pct": Decimal(str(round(pnl_pct, 4))),
                    "signal_reasoning": pos["reasoning"],
                })

        for trade in trades:
            BacktestTrade.objects.create(run=run, **trade)

        total_return = (capital - float(initial_capital)) / float(initial_capital) * 100
        wins = [t for t in trades if t["pnl"] and float(t["pnl"]) > 0]
        losses = [t for t in trades if t["pnl"] and float(t["pnl"]) <= 0]
        win_rate = len(wins) / len(trades) * 100 if trades else 0
        avg_win = sum(float(t["pnl_pct"]) for t in wins) / len(wins) if wins else 0
        avg_loss = sum(float(t["pnl_pct"]) for t in losses) / len(losses) if losses else 0

        returns = [float(t["pnl_pct"]) for t in trades if t["pnl_pct"]]
        sharpe = _compute_sharpe(returns)

        max_dd = _compute_max_drawdown(capital, trades)

        run.final_value = Decimal(str(round(capital, 2)))
        run.total_return_pct = Decimal(str(round(total_return, 4)))
        run.win_rate = Decimal(str(round(win_rate, 4)))
        run.max_drawdown_pct = Decimal(str(round(max_dd, 4)))
        run.sharpe_ratio = Decimal(str(round(sharpe, 4)))
        run.total_trades = len(trades)
        run.winning_trades = len(wins)
        run.losing_trades = len(losses)
        run.avg_win_pct = Decimal(str(round(avg_win, 4)))
        run.avg_loss_pct = Decimal(str(round(avg_loss, 4)))
        run.status = "completed"
        run.save()

        return run

    except Exception as e:
        run.status = "failed"
        run.raw_results = {"error": str(e)}
        run.save()
        return run


def _compute_sharpe(returns):
    if len(returns) < 2:
        return 0
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    std = math.sqrt(variance)
    return mean / std * math.sqrt(252) if std > 0 else 0


def _compute_max_drawdown(final_capital, trades):
    return 0