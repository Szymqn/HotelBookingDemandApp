from django.urls import path
from .views import log_in_page, sign_up_page, log_out_page

# Define URL patterns
urlpatterns = [
    path('sign_up/', sign_up_page, name='sign_up'),
    path('log_in/', log_in_page, name='log_in'),
    path('log_out/', log_out_page, name='log_out'),
]
