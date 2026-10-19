from django.urls import path
from . import views

app_name = "tickers"

urlpatterns = [
    path("", views.ticker_list, name="list"),
    path("<str:symbol>/", views.ticker_detail, name="detail"),
    path("<str:symbol>/refresh/", views.ticker_refresh, name="refresh"),
]