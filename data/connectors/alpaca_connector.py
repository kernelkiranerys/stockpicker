from datetime import datetime, timezone
from decimal import Decimal
from django.conf import settings

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
    from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
    from alpaca.data.historical.stock import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
    from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
    HAS_ALPACA = True
except ImportError:
    HAS_ALPACA = False


_clients = {}


def _get_trading_client():
    if not HAS_ALPACA or not settings.ALPACA_API_KEY:
        return None
    if "trading" not in _clients:
        _clients["trading"] = TradingClient(
            settings.ALPACA_API_KEY,
            settings.ALPACA_SECRET_KEY,
            paper=settings.ALPACA_PAPER,
        )
    return _clients["trading"]


def _get_data_client():
    if not HAS_ALPACA or not settings.ALPACA_API_KEY:
        return None
    if "data" not in _clients:
        _clients["data"] = StockHistoricalDataClient(
            settings.ALPACA_API_KEY,
            settings.ALPACA_SECRET_KEY,
        )
    return _clients["data"]


def get_account():
    """Get Alpaca paper trading account info."""
    client = _get_trading_client()
    if not client:
        return None
    try:
        account = client.get_account()
        return {
            "cash": float(account.cash),
            "portfolio_value": float(account.portfolio_value),
            "buying_power": float(account.buying_power),
            "equity": float(account.equity),
            "pnl": float(account.unrealized_pl),
            "pnl_pct": float(account.unrealized_plpc) if account.unrealized_plpc else 0,
        }
    except Exception:
        return None


def get_positions():
    """Get all open positions from Alpaca."""
    client = _get_trading_client()
    if not client:
        return []
    try:
        positions = client.get_all_positions()
        return [
            {
                "symbol": p.symbol,
                "qty": float(p.qty),
                "avg_entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price),
                "market_value": float(p.market_value),
                "unrealized_pnl": float(p.unrealized_pl),
                "unrealized_pnl_pct": float(p.unrealized_plpc) if p.unrealized_plpc else 0,
            }
            for p in positions
        ]
    except Exception:
        return []


def submit_market_order(symbol, qty, side="buy"):
    """Submit a market order to Alpaca paper trading.
    side: 'buy' or 'sell'
    """
    client = _get_trading_client()
    if not client:
        return None
    try:
        order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )
        order = client.submit_order(order_data)
        return {
            "id": str(order.id),
            "symbol": order.symbol,
            "qty": float(order.qty),
            "side": order.side.value if hasattr(order.side, "value") else str(order.side),
            "status": order.status,
            "created_at": str(order.created_at),
        }
    except Exception as e:
        return {"error": str(e)}


def get_latest_quote(symbol):
    """Get latest quote from Alpaca."""
    client = _get_data_client()
    if not client:
        return None
    try:
        request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
        quotes = client.get_stock_latest_quote(request)
        if symbol in quotes:
            q = quotes[symbol]
            return {
                "bid": float(q.bid_price),
                "ask": float(q.ask_price),
                "bid_size": float(q.bid_size),
                "ask_size": float(q.ask_size),
                "timestamp": q.timestamp,
            }
    except Exception:
        pass
    return None


def fetch_bars(symbol, timeframe="1Min", limit=390):
    """Fetch intraday bars from Alpaca.
    timeframe: '1Min', '5Min', '15Min', '1Hour', '1Day'
    limit: number of bars (390 = 1 full trading day of 1-min bars)
    """
    client = _get_data_client()
    if not client:
        return []
    tf_map = {
        "1Min": TimeFrame(1, TimeFrameUnit.Minute),
        "5Min": TimeFrame(5, TimeFrameUnit.Minute),
        "15Min": TimeFrame(15, TimeFrameUnit.Minute),
        "1Hour": TimeFrame(1, TimeFrameUnit.Hour),
        "1Day": TimeFrame(1, TimeFrameUnit.Day),
    }
    try:
        from datetime import datetime, timedelta
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=5)
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=tf_map.get(timeframe, tf_map["1Min"]),
            start=start,
            end=end,
            limit=limit,
        )
        bars = client.get_stock_bars(request)
        if symbol in bars:
            return [
                {
                    "timestamp": bar.timestamp,
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": int(bar.volume),
                    "vwap": float(bar.vwap) if bar.vwap else None,
                }
                for bar in bars[symbol]
            ]
    except Exception:
        pass
    return []


def close_all_positions():
    """Close all positions (for sandbox reset)."""
    client = _get_trading_client()
    if not client:
        return None
    try:
        client.close_all_positions(cancel_orders=True)
        return True
    except Exception:
        return False