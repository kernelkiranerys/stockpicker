from django.shortcuts import render
from django.core.paginator import Paginator
from signals.models import Signal


def signal_list(request):
    qs = Signal.objects.select_related("ticker").order_by("-created_at")
    sig_type = request.GET.get("type")
    if sig_type:
        qs = qs.filter(signal_type=sig_type)
    paginator = Paginator(qs, 50)
    page = request.GET.get("page", 1)
    page_obj = paginator.get_page(page)
    return render(request, "signals/list.html", {"page_obj": page_obj, "current_type": sig_type})


def screener(request):
    day_trade = list(Signal.objects.filter(signal_type="day_trade", is_active=True).select_related("ticker").order_by("-confidence")[:20])
    medium = list(Signal.objects.filter(signal_type="medium_turnaround", is_active=True).select_related("ticker").order_by("-confidence")[:20])
    seasonal = list(Signal.objects.filter(signal_type="seasonal_swing", is_active=True).select_related("ticker").order_by("-confidence")[:20])
    return render(request, "signals/screener.html", {
        "day_trade": day_trade,
        "medium": medium,
        "seasonal": seasonal,
    })