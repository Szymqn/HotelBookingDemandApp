from . import views
from django.urls import path

urlpatterns = [
    path('cities/search/', views.CitySearchAPIView.as_view(), name='city-search'),
]
