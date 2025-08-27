from django.urls import path
from .views import login_page, sign_in_page, logout_page

# Define URL patterns
urlpatterns = [
    path('login/', login_page, name='login'),
    path('sign_in/', sign_in_page, name='sign_in'),
    path('logout/', logout_page, name='logout'),
]
