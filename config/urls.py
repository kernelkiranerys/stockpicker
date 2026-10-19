from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("dashboard/", include("dashboard.urls")),
    path("tickers/", include("tickers.urls")),
    path("sandbox/", include("sandbox.urls")),
    path("knowledge/", include("knowledge.urls")),
    path("signals/", include("signals.urls")),
    path("signallog/", include("signallog.urls")),
    path("screener/", include("screener.urls")),
    path("backtest/", include("backtest.urls")),
    path("feedback/", include("feedback.urls")),
    path("supplychain/", include("supplychain.urls")),
    path("", RedirectView.as_view(url="/dashboard/")),
]