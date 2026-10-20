from django.urls import path
from . import views

app_name = "signallog"

urlpatterns = [
    path("", views.signal_log, name="log"),
]