from django.db.models import Avg, F
from django.shortcuts import render

from bookings.models import Booking


# Create your views here.
def index(request):
    total_bookings = Booking.objects.all().count()

    avg_adr = Booking.objects.aggregate(Avg('adr'))['adr__avg']

    avg_room_occupy = Booking.objects.annotate(
        total_nights=F('stays_in_weekend_nights') + F('stays_in_week_nights')
    ).aggregate(avg_total_nights=Avg('total_nights'))['avg_total_nights']

    return render(
        request,
        "dashboard/index.html",
        {
            'total_bookings': total_bookings,
            'avg_adr': round(avg_adr, 2),
            'avg_room_occupy': round(avg_room_occupy, 2),
        }
    )
