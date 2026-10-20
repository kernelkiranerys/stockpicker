from django.urls import path
from . import views

app_name = "signals"

urlpatterns = [
    path("", views.signal_list, name="list"),
    path("screener/", views.screener, name="screener"),
]