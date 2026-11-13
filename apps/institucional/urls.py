from django.urls import path

from . import views

app_name = "institucional"

urlpatterns = [
    path("", views.home, name="home"),
    path("contato/", views.contato, name="contato"),
]
