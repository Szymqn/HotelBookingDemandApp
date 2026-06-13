import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HotelBookingDemandApp.settings")

app = Celery("HotelBookingDemandApp")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
