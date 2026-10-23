from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.market_overview, name="overview"),
    path("watchlist/", views.watchlist, name="watchlist"),
    path("rotation/", views.industry_rotation, name="rotation"),
]