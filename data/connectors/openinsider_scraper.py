import requests
from bs4 import BeautifulSoup
from datetime import datetime, date as date_cls
from decimal import Decimal
from collections import defaultdict


BASE_URL = "http://openinsider.com"


def fetch_insider_trades(ticker_symbol, days=30):
    """Scrape OpenInsider.com for recent insider trades.
    Returns list of dicts with parsed Form 4 data.
    """
    url = f"{BASE_URL}/screener?s={ticker_symbol}&o=&pl=&ph=&ll=&lh=&fd=30&td=0&tdo=&d=&dop=&dod=&olp=&oln=&oll=&olh=&lop=&lon=&lolh=&loh=&days={days}&fily=&filyt=&filyi=&filysf=&filysa=&g=&g1=&g2=&g3=&g4=&nn=&n=&donly=&rico=&v=&vl=&vh=&il=&ih=&o=&fd=30"
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            return []
    except Exception:
        return []

    soup = BeautifulSoup(resp.content, "lxml")
    table = soup.find("table", {"class": "tinytable"})
    if not table:
        return []

    rows = table.find_all("tr")
    trades = []
    for row in rows[1:]:
        cells = row.find_all("td")
        if len(cells) < 13:
            continue
        try:
            filing_date_str = cells[0].text.strip()
            trade_date_str = cells[1].text.strip()
            ticker = cells[2].text.strip()
            insider_name = cells[3].text.strip()
            title = cells[4].text.strip()
            trade_type = cells[5].text.strip()
            shares_str = cells[6].text.strip().replace(",", "")
            price_str = cells[7].text.strip().replace("$", "").replace(",", "")
            value_str = cells[11].text.strip().replace("$", "").replace(",", "")

            filing_date = _parse_date(filing_date_str)
            trade_date = _parse_date(trade_date_str)

            shares = Decimal(shares_str) if shares_str else Decimal("0")
            price = Decimal(price_str) if price_str else None
            value = Decimal(value_str) if value_str else Decimal("0")

            is_open_market = "P" in trade_type.upper() or "PURCHASE" in trade_type.upper()
            is_sale = "S" in trade_type.upper() or "SALE" in trade_type.upper()
            is_option = "O" in trade_type.upper() or "OPTION" in trade_type.upper()

            trades.append({
                "filing_date": filing_date,
                "trade_date": trade_date,
                "ticker": ticker,
                "insider_name": insider_name,
                "title": title,
                "transaction_type": trade_type,
                "shares": shares,
                "price": price,
                "value": value,
                "is_open_market": is_open_market,
                "is_sale": is_sale,
                "is_option": is_option,
                "source": "openinsider",
                "filing_url": f"{BASE_URL}/screener?s={ticker}",
            })
        except Exception:
            continue

    return trades


def detect_cluster_buying(ticker_symbol, days=30, min_buyers=3):
    """Detect cluster insider buying (multiple insiders buying in same period).
    This is a strong bullish signal per professional analysis.
    Returns dict with cluster info.
    """
    trades = fetch_insider_trades(ticker_symbol, days=days)

    open_market_buys = [t for t in trades if t.get("is_open_market") and not t.get("is_option")]
    officers = [t for t in open_market_buys if t.get("title") and
                any(w in t["title"].upper() for w in ["CEO", "CFO", "COO", "OFFICER", "PRESIDENT", "VP"])]

    unique_insiders = set(t["insider_name"] for t in open_market_buys)
    unique_officers = set(t["insider_name"] for t in officers)

    total_shares = sum(t["shares"] for t in open_market_buys)
    total_value = sum(t["value"] for t in open_market_buys)

    is_cluster = len(unique_insiders) >= min_buyers
    is_officer_cluster = len(unique_officers) >= min_buyers

    return {
        "total_trades": len(trades),
        "open_market_buys": len(open_market_buys),
        "officer_buys": len(officers),
        "unique_insider_count": len(unique_insiders),
        "unique_officer_count": len(unique_officers),
        "is_cluster": is_cluster,
        "is_officer_cluster": is_officer_cluster,
        "total_shares_bought": total_shares,
        "total_value": total_value,
        "signals": _build_cluster_signals(is_cluster, is_officer_cluster, len(unique_insiders), days),
    }


def _build_cluster_signals(is_cluster, is_officer_cluster, count, days):
    signals = []
    if is_officer_cluster:
        signals.append(f"Officer cluster buying detected ({count} officers in {days} days) — strong bullish")
    if is_cluster and not is_officer_cluster:
        signals.append(f"Insider cluster buying ({count} insiders in {days} days) — bullish")
    if count == 0:
        signals.append("No open market insider buying")
    return signals


def _parse_date(date_str):
    """Parse OpenInsider date format (e.g. '2024-Oct-15 14:30:21')."""
    try:
        return datetime.strptime(date_str[:10], "%Y-%b-%d").date()
    except (ValueError, IndexError):
        try:
            return date_cls.fromisoformat(date_str[:10])
        except Exception:
            return date_cls.today()