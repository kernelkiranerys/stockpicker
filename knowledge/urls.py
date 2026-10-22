from django.urls import path
from . import views

app_name = "knowledge"

urlpatterns = [
    path("", views.knowledge_list, name="list"),
    path("upload/", views.knowledge_upload, name="upload"),
    path("<int:doc_id>/", views.knowledge_detail, name="detail"),
    path("<int:doc_id>/delete/", views.knowledge_delete, name="delete"),
]