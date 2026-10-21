from django.shortcuts import render
from backtest.models import BacktestRun


def index(request):
    runs = BacktestRun.objects.all().order_by("-created_at")[:20]
    return render(request, "backtest/index.html", {"runs": runs})