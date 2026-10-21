from screener.models import RegimeSnapshot
from signals.engine_regime import detect_regime
from decimal import Decimal
from django.utils import timezone as djtz


def run_regime_detection():
    """Stage 4: Detect current market regime and determine strategy mode.
    Creates a RegimeSnapshot record.
    Returns the regime dict.
    """
    result = detect_regime()
    today = djtz.now().date()

    snapshot, _ = RegimeSnapshot.objects.update_or_create(
        date=today,
        defaults={
            "regime": result["regime"],
            "strategy_mode": result["strategy_mode"],
            "vix": Decimal(str(result["vix"])) if result.get("vix") else None,
            "treasury_10y": Decimal(str(result["treasury_10y"])) if result.get("treasury_10y") else None,
            "yield_delta_30d": Decimal(str(result["yield_delta_30d"])) if result.get("yield_delta_30d") else None,
            "yield_curve": Decimal(str(result["yield_curve"])) if result.get("yield_curve") else None,
            "spy_trend": result.get("spy_trend", ""),
            "score": Decimal(str(result["score"])),
            "signals": result["signals"],
        },
    )

    return result