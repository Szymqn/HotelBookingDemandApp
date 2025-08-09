from django.shortcuts import render
from django_tables2 import RequestConfig

from .models import Booking
from .tables import BookingTable


# Create your views here.

def index(request):
    table = BookingTable(Booking.objects.all())
    RequestConfig(request, paginate={"per_page": 10}).configure(table)
    return render(request, 'bookings/index.html', {'table': table})
