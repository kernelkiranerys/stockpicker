import requests
from datetime import datetime, timezone
from decimal import Decimal
from django.conf import settings

BASE_URL = "https://financialmodelingprep.com/api/v3"


def _get_key():
    return settings.FMP_API_KEY


def fetch_income_statement(ticker):
    """Fetch annual income statement from FMP."""
    key = _get_key()
    if not key:
        return None
    try:
        resp = requests.get(
            f"{BASE_URL}/income-statement/{ticker.yf_symbol}",
            params={"apikey": key, "limit": 5},
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception:
        return None


def fetch_balance_sheet(ticker):
    """Fetch annual balance sheet from FMP."""
    key = _get_key()
    if not key:
        return None
    try:
        resp = requests.get(
            f"{BASE_URL}/balance-sheet-statement/{ticker.yf_symbol}",
            params={"apikey": key, "limit": 5},
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception:
        return None


def fetch_cash_flow(ticker):
    """Fetch annual cash flow statement from FMP."""
    key = _get_key()
    if not key:
        return None
    try:
        resp = requests.get(
            f"{BASE_URL}/cash-flow-statement/{ticker.yf_symbol}",
            params={"apikey": key, "limit": 5},
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception:
        return None


def fetch_ratios(ticker):
    """Fetch financial ratios (P/E, P/B, debt/equity, etc.) from FMP."""
    key = _get_key()
    if not key:
        return None
    try:
        resp = requests.get(
            f"{BASE_URL}/ratios/{ticker.yf_symbol}",
            params={"apikey": key, "limit": 5},
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception:
        return None


def fetch_key_metrics(ticker):
    """Fetch key metrics (market cap, EV/EBITDA, etc.) from FMP."""
    key = _get_key()
    if not key:
        return None
    try:
        resp = requests.get(
            f"{BASE_URL}/key-metrics/{ticker.yf_symbol}",
            params={"apikey": key, "limit": 5},
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception:
        return None


def fetch_enterprise_value(ticker):
    """Fetch enterprise value data from FMP."""
    key = _get_key()
    if not key:
        return None
    try:
        resp = requests.get(
            f"{BASE_URL}/enterprise-values/{ticker.yf_symbol}",
            params={"apikey": key, "limit": 5},
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception:
        return None


def fetch_fundamental_data(ticker):
    """Fetch comprehensive fundamental data from FMP.
    Returns a dict with all fundamental data combined.
    """
    key = _get_key()
    if not key:
        return None

    income = fetch_income_statement(ticker) or []
    balance = fetch_balance_sheet(ticker) or []
    cashflow = fetch_cash_flow(ticker) or []
    ratios = fetch_ratios(ticker) or []
    metrics = fetch_key_metrics(ticker) or []

    if not income:
        return None

    latest_income = income[0] if income else {}
    latest_balance = balance[0] if balance else {}
    latest_ratios = ratios[0] if ratios else {}
    latest_metrics = metrics[0] if metrics else {}

    pe_5yr = [r.get("peRatio") for r in ratios if r.get("peRatio")][:5]
    pe_current = latest_ratios.get("peRatio")
    pe_percentile = _percentile_rank(pe_current, pe_5yr) if pe_current and pe_5yr else None

    return {
        "revenue": latest_income.get("revenue"),
        "net_income": latest_income.get("netIncome"),
        "eps": latest_income.get("eps"),
        "gross_profit": latest_income.get("grossProfit"),
        "operating_income": latest_income.get("operatingIncome"),
        "total_debt": latest_balance.get("totalDebt"),
        "total_assets": latest_balance.get("totalAssets"),
        "total_equity": latest_balance.get("totalStockholdersEquity"),
        "free_cash_flow": latest_metrics.get("freeCashFlowFlowing"),
        "pe_ratio": pe_current,
        "pb_ratio": latest_ratios.get("pbRatio"),
        "debt_to_equity": latest_ratios.get("debtEquityRatio"),
        "current_ratio": latest_ratios.get("currentRatio"),
        "roe": latest_ratios.get("returnOnEquity"),
        "roa": latest_ratios.get("returnOnAssets"),
        "revenue_growth": latest_income.get("revenueGrowth"),
        "gross_margin": latest_income.get("grossProfitMargin"),
        "net_margin": latest_income.get("netProfitMargin"),
        "pe_5yr_range": pe_5yr,
        "pe_percentile": pe_percentile,
        "raw": {
            "income": income[:3],
            "balance": balance[:3],
            "ratios": ratios[:3],
            "metrics": metrics[:3],
        },
    }


def _percentile_rank(value, values):
    """Calculate where a value sits in a list (0-100 percentile)."""
    if not values or value is None:
        return None
    try:
        v = float(value)
        below = sum(1 for x in values if x is not None and float(x) < v)
        return round(below / len(values) * 100, 1)
    except (ValueError, TypeError):
        return None