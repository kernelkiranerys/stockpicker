import requests
from datetime import datetime, date as date_cls, timezone
from decimal import Decimal


BASE_URL = "https://data.sec.gov/submissions"


def _get_headers():
    return {
        "User-Agent": "stockpicker/1.0 contact@example.com",
        "Accept-Encoding": "gzip, deflate",
        "Host": "data.sec.gov",
    }


def fetch_form4(ticker):
    try:
        resp = requests.get(
            f"{BASE_URL}/CIK{ticker.symbol}.json",
            headers=_get_headers(),
            timeout=10,
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        cik = data.get("CIK", "").lstrip("0")
        if not cik:
            return []
    except Exception:
        return []

    try:
        resp = requests.get(
            f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json",
            headers=_get_headers(),
            timeout=10,
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
    except Exception:
        return []

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accession_numbers = recent.get("accessionNo", [])
    primary_docs = recent.get("primaryDocument", [])
    primary_descs = recent.get("primaryDocDescription", [])

    results = []
    for i, form_type in enumerate(forms):
        if form_type != "4":
            continue
        try:
            filing_date_str = dates[i] if i < len(dates) else ""
            filing_date = date_cls.fromisoformat(filing_date_str) if filing_date_str else datetime.now(timezone.utc).date()
            accession = accession_numbers[i] if i < len(accession_numbers) else ""
            accession_clean = accession.replace("-", "")
            doc = primary_docs[i] if i < len(primary_docs) else ""
            filing_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik.zfill(10)}&type=4&date=&owner=only"

            results.append({
                "filing_date": filing_date,
                "insider_name": "Unknown",
                "title": "Unknown",
                "transaction_type": "UNKNOWN",
                "shares": Decimal("0"),
                "price": None,
                "value": Decimal("0"),
                "filing_url": filing_url,
                "raw": {"form": "4", "accession": accession, "cik": cik},
            })
        except Exception:
            continue

    return results[:20]


def fetch_13f(ticker):
    try:
        resp = requests.get(
            f"{BASE_URL}/CIK{ticker.symbol}.json",
            headers=_get_headers(),
            timeout=10,
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        cik = data.get("CIK", "").lstrip("0")
        if not cik:
            return []
    except Exception:
        return []

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])

    results = []
    for i, form_type in enumerate(forms):
        if form_type not in ("13F-HR", "13F-NT"):
            continue
        try:
            filing_date_str = dates[i] if i < len(dates) else ""
            filing_date = date_cls.fromisoformat(filing_date_str) if filing_date_str else datetime.now(timezone.utc).date()
            results.append({
                "filing_date": filing_date,
                "filer_name": data.get("name", "Unknown"),
                "shares": Decimal("0"),
                "value": Decimal("0"),
                "filing_url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik.zfill(10)}&type=13F",
                "raw": {"form": form_type, "cik": cik},
            })
        except Exception:
            continue

    return results[:10]