from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="analytics"),
    path("status/", views.status, name="analytics_status"),
]
