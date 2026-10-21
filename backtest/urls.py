from django.urls import path
from . import views

app_name = "backtest"

urlpatterns = [
    path("", views.index, name="index"),
]
