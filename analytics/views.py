import calendar
import json

from django.db.models import Avg, F, Count
from django.shortcuts import render

from bookings.models import Booking


# Create your views here.
def index(request):
    avg_adr = Booking.objects.aggregate(Avg('adr'))['adr__avg']

    avg_room_occupy = Booking.objects.annotate(
        total_nights=F('stays_in_weekend_nights') + F('stays_in_week_nights')
    ).aggregate(avg_total_nights=Avg('total_nights'))['avg_total_nights']

    raw = (Booking.objects
           .values('arrival_date_year', 'arrival_date_month_number')
           .annotate(bookings=Count('id'), m_avg_adr=Avg('adr'))
           .order_by('arrival_date_year', 'arrival_date_month_number'))

    labels, bookings_data, adr_data = [], [], []
    for r in raw:
        if r['bookings'] <= 0:
            continue
        m_abbr = calendar.month_abbr[r['arrival_date_month_number']]
        labels.append(f"{m_abbr} {r['arrival_date_year']}")
        bookings_data.append(r['bookings'])
        adr_data.append(round(r['m_avg_adr'] or 0, 2))

    context = {
        'avg_adr': round(avg_adr or 0, 2),
        'avg_room_occupy': round(avg_room_occupy or 0, 2),
        'chart_label_json': json.dumps(labels),
        'chart_data_json': json.dumps(bookings_data),
        'chart_adr_json': json.dumps(adr_data),
    }
    return render(request, "analytics/index.html", context)
