from django.urls import path
from . import views

app_name = "supplychain"

urlpatterns = [
    path("", views.index, name="index"),
]
