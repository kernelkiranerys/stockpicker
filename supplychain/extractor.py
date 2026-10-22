import requests
from bs4 import BeautifulSoup
from datetime import datetime, date as date_cls
from decimal import Decimal
from supplychain.models import CompanyRelationship
from ai_expert.ollama_client import chat
from django.conf import settings
import json


BASE_URL = "https://www.sec.gov/cgi-bin/browse-edgar"

HEADERS = {
    "User-Agent": "stockpicker/1.0 contact@example.com",
    "Accept-Encoding": "gzip, deflate",
    "Host": "www.sec.gov",
}


def extract_relationships(ticker):
    """Pull 10-K sections from SEC EDGAR and extract supply chain relationships via LLM.

    Steps:
    1. Get latest 10-K filing URL from EDGAR
    2. Fetch the "Business" and "Risk Factors" sections
    3. Send to LLM: "Extract all named customers, suppliers, and competitors"
    4. Store as CompanyRelationship records
    """
    filing_info = _get_latest_10k(ticker)
    if not filing_info:
        return []

    filing_url = filing_info.get("url", "")
    filing_date = filing_info.get("date")
    sections_text = _fetch_10k_sections(filing_url)

    if not sections_text:
        return []

    relationships = _llm_extract_relationships(ticker, sections_text, filing_url, filing_date)
    return relationships


def _get_latest_10k(ticker):
    """Find the latest 10-K filing for a ticker on SEC EDGAR."""
    try:
        resp = requests.get(
            "https://data.sec.gov/submissions/CIK" + _get_cik(ticker).zfill(10) + ".json",
            headers=HEADERS,
            timeout=15,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accession = recent.get("accessionNo", [])
        primary_docs = recent.get("primaryDocument", [])

        for i, form_type in enumerate(forms):
            if form_type == "10-K":
                acc = accession[i].replace("-", "")
                doc = primary_docs[i] if i < len(primary_docs) else ""
                url = f"https://www.sec.gov/Archives/edgar/data/{_get_cik(ticker)}/{acc}/{doc}"
                filing_date = None
                if i < len(dates):
                    try:
                        filing_date = date_cls.fromisoformat(dates[i])
                    except Exception:
                        pass
                return {"url": url, "date": filing_date, "accession": accession[i]}
    except Exception:
        pass
    return None


def _get_cik(ticker):
    """Get CIK number for a ticker (simplified — uses symbol mapping)."""
    symbol_to_cik = {
        "AMZN": "1018724",
        "XOM": "34088",
        "CF": "1324404",
        "NTR": "1521332",
        "MOS": "1285785",
        "DAL": "27904",
        "UAL": "1005174",
        "AAL": "280796",
    }
    return symbol_to_cik.get(ticker.symbol, "")


def _fetch_10k_sections(filing_url):
    """Fetch and extract Business and Risk Factors sections from 10-K."""
    try:
        resp = requests.get(filing_url, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.content, "lxml")
        text = soup.get_text(separator=" ", strip=True)

        business_start = text.find("BUSINESS")
        risk_start = text.find("RISK FACTORS")

        sections = ""
        if business_start >= 0 and risk_start >= 0:
            end = min(business_start + 50000, risk_start)
            sections = text[business_start:end]
        elif business_start >= 0:
            sections = text[business_start:business_start + 30000]

        return sections[:30000]
    except Exception:
        return ""


def _llm_extract_relationships(ticker, text, filing_url, filing_date):
    """Use LLM to extract named customers, suppliers, competitors from 10-K text."""
    prompt = f"""Extract all named customers, suppliers, and competitors from this 10-K filing text for {ticker.name}.

Text (excerpt from 10-K):
{text[:20000]}

Return JSON array of objects: {{"company": "<name>", "type": "<customer|supplier|competitor>", "context": "<source sentence>"}}

Only include explicitly named companies. Do not infer."""

    model = settings.OLLAMA_MODEL_FAST
    raw = chat(model, "You are a financial data extraction expert.", prompt, temperature=0.1, num_predict=600)

    relationships = []
    try:
        import re
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            for item in data:
                company = item.get("company", "").strip()
                rel_type = item.get("type", "").strip().lower()
                context = item.get("context", "")[:500]

                if not company or rel_type not in ["customer", "supplier", "competitor", "partner", "distributor"]:
                    continue

                rel, created = CompanyRelationship.objects.get_or_create(
                    source_ticker=ticker,
                    target_company=company,
                    relationship_type=rel_type,
                    defaults={
                        "context": context,
                        "filing_date": filing_date,
                        "filing_url": filing_url,
                    },
                )
                relationships.append(rel)
    except (json.JSONDecodeError, ValueError):
        pass

    return relationships