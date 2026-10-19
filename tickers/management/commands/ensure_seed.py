from decimal import Decimal
from django.core.management.base import BaseCommand
from tickers.models import Exchange, Sector, Industry, Ticker, Watchlist
from sandbox.models import Portfolio

EXCHANGES = [
    ("NYSE", "New York Stock Exchange", "US"),
    ("NASDAQ", "NASDAQ", "US"),
    ("LSE", "London Stock Exchange", "UK"),
]

SECTORS = [
    "Technology",
    "Energy",
    "Materials",
    "Industrials",
    "Consumer Discretionary",
]

TICKERS = [
    ("AMZN", "Amazon.com Inc", "NASDAQ", "Consumer Discretionary", "USD", ""),
    ("CNA", "Centrica plc", "LSE", "Energy", "GBP", ".L"),
    ("CF", "CF Industries Holding", "NYSE", "Materials", "USD", ""),
    ("NTR", "Nutrien Ltd", "NYSE", "Materials", "USD", ""),
    ("MOS", "Mosaic Co", "NYSE", "Materials", "USD", ""),
    ("DAL", "Delta Air Lines", "NYSE", "Industrials", "USD", ""),
    ("UAL", "United Airlines Holdings", "NASDAQ", "Industrials", "USD", ""),
    ("AAL", "American Airlines Group", "NASDAQ", "Industrials", "USD", ""),
    ("IAG", "International Airlines Group", "LSE", "Industrials", "GBP", ".L"),
    ("XOM", "Exxon Mobil Corp", "NYSE", "Energy", "USD", ""),
]

PORTFOLIOS = [
    ("Day Trader", "day_trade"),
    ("Swing", "medium_turnaround"),
    ("Seasonal", "seasonal_swing"),
]


class Command(BaseCommand):
    help = "Seed exchanges, sectors, tickers, watchlist, and sandbox portfolios"

    def handle(self, *args, **options):
        for code, name, country in EXCHANGES:
            Exchange.objects.get_or_create(code=code, defaults={"name": name, "country": country})
        self.stdout.write(f"Ensured {len(EXCHANGES)} exchanges")

        sector_objs = {}
        for name in SECTORS:
            sector, _ = Sector.objects.get_or_create(name=name)
            sector_objs[name] = sector
        self.stdout.write(f"Ensured {len(SECTORS)} sectors")

        created_count = 0
        for symbol, name, ex_code, sector_name, currency, yf_suffix in TICKERS:
            exchange = Exchange.objects.get(code=ex_code)
            sector = sector_objs.get(sector_name)
            industry = None
            if sector:
                industry, _ = Industry.objects.get_or_create(name=f"{sector_name} General", defaults={"sector": sector})
            _, created = Ticker.objects.get_or_create(
                symbol=symbol,
                defaults={
                    "name": name,
                    "exchange": exchange,
                    "sector": sector,
                    "industry": industry,
                    "currency": currency,
                    "yf_suffix": yf_suffix,
                },
            )
            if created:
                created_count += 1
        self.stdout.write(f"Ensured {len(TICKERS)} tickers ({created_count} new)")

        wl, created = Watchlist.objects.get_or_create(
            name="Seasonal Swing",
            defaults={"description": "Primary watchlist: AMZN, Centrica, fertilizer, airlines, XOM", "is_active": True},
        )
        for symbol, *_ in TICKERS:
            t = Ticker.objects.get(symbol=symbol)
            wl.tickers.add(t)
        self.stdout.write(f"Ensured watchlist '{wl.name}' with {wl.tickers.count()} tickers")

        for name, mode in PORTFOLIOS:
            Portfolio.objects.get_or_create(
                name=name,
                signal_mode=mode,
                defaults={
                    "starting_cash": Decimal("10000"),
                    "cash": Decimal("10000"),
                    "is_active": True,
                },
            )
        self.stdout.write(f"Ensured {len(PORTFOLIOS)} sandbox portfolios")

        self.stdout.write(self.style.SUCCESS("Seed complete."))