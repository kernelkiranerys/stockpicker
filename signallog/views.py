from django.shortcuts import render
from signallog.models import SignalLogEntry


def signal_log(request):
    entries = SignalLogEntry.objects.select_related("signal", "signal__ticker").order_by("-recorded_at")[:200]
    total = entries.count()
    wins = sum(1 for e in entries if e.outcome == "win")
    losses = sum(1 for e in entries if e.outcome == "loss")
    pending = sum(1 for e in entries if e.outcome == "pending" or not e.outcome)
    hit_rate = (wins / total * 100) if total > 0 else 0
    return render(request, "signallog/log.html", {
        "entries": entries,
        "total": total,
        "wins": wins,
        "losses": losses,
        "pending": pending,
        "hit_rate": round(hit_rate, 1),
    })