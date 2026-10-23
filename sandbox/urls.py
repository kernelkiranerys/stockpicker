from django.urls import path
from . import views

app_name = "sandbox"

urlpatterns = [
    path("", views.sandbox_overview, name="overview"),
    path("<int:portfolio_id>/", views.sandbox_detail, name="detail"),
    path("<int:portfolio_id>/reset/", views.sandbox_reset, name="reset"),
    path("<int:portfolio_id>/equity/", views.equity_data, name="equity_data"),
    path("<int:portfolio_id>/trades/", views.trades_data, name="trades_data"),
]