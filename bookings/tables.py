import django_tables2 as tables

from .models import Booking


class BookingTable(tables.Table):
    class Meta:
        model = Booking
        template_name = "django_tables2/semantic.html"
        attrs = {"class": "ui celled striped table"}
