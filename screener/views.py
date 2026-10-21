from django.shortcuts import render
from screener.models import ScreenedUniverse, RegimeSnapshot
from django.utils import timezone as djtz


def index(request):
    today = djtz.now().date()
    latest_screen = ScreenedUniverse.objects.filter(screen_date=today).order_by("-rank", "-conviction_score")
    regime = RegimeSnapshot.objects.order_by("-date").first()

    if not latest_screen.exists():
        latest_screen = ScreenedUniverse.objects.order_by("-screen_date", "-rank")

    high_conviction = [s for s in latest_screen if s.conviction_score >= 75]
    medium_conviction = [s for s in latest_screen if 50 <= s.conviction_score < 75]

    return render(request, "screener/index.html", {
        "screened": latest_screen[:50],
        "high_conviction": high_conviction,
        "medium_conviction": medium_conviction,
        "regime": regime,
        "total": latest_screen.count(),
    })