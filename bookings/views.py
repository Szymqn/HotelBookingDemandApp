from django.shortcuts import render
from django.db.models import Avg, F, ExpressionWrapper, IntegerField, Case, When, FloatField

from django_tables2 import RequestConfig

from .models import Booking
from .tables import BookingTable

from constants import TEST_DATE


# Create your views here.

def index(request):
    total_bookings = Booking.objects.all().count()

    bookings_in_month = Booking.objects.filter(
        arrival_date_month_number__exact=TEST_DATE.month,
        arrival_date_year__exact=TEST_DATE.year,
    )

    total_nights_expr = ExpressionWrapper(
        F('stays_in_week_nights') + F('stays_in_weekend_nights'),
        output_field=IntegerField()
    )

    avg_stay_per_month = bookings_in_month.aggregate(
        avg_stay=Avg(total_nights_expr)
    )['avg_stay'] or 0

    avg_cancellation_rate = bookings_in_month.aggregate(
        rate=Avg(
            Case(
                When(is_cancelled=True, then=1),
                default=0,
                output_field=FloatField()
            )
        )
    )['rate'] or 0

    table = BookingTable(Booking.objects.all())
    RequestConfig(request, paginate={"per_page": 10}).configure(table)

    return render(
        request,
        'bookings/index.html',
        {
            'total_bookings': total_bookings,
            'avg_stay_per_month': round(avg_stay_per_month, 2),
            'avg_cancellation_rate': round(avg_cancellation_rate, 2),
            'table': table,
        }
    )
