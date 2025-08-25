import django_tables2 as tables

from .models import Booking


class BookingTable(tables.Table):
    class Meta:
        model = Booking
        template_name = "django_tables2/bootstrap5.html"
        attrs = {
            'class': 'table table-striped table-hover table-bordered table-sm table-nowrap',
            'style': 'min-width:900px;'
        }
        order_by = ['-arrival_date']
