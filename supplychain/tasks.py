from celery import shared_task
from supplychain.extractor import extract_relationships
from tickers.models import Ticker, Watchlist


@shared_task
def extract_supply_chains():
    """Quarterly: Extract supply chain relationships from latest 10-Ks."""
    wl = Watchlist.objects.filter(is_active=True).first()
    tickers = list(wl.tickers.all()) if wl else list(Ticker.objects.filter(is_active=True))
    total = 0
    for ticker in tickers:
        try:
            rels = extract_relationships(ticker)
            total += len(rels)
        except Exception:
            pass
    return {"relationships_extracted": total}