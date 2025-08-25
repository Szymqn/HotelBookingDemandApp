import calendar
import json

from django.db.models import Avg, F, Count
from django.shortcuts import render

from bookings.models import Booking


# Create your views here.
def index(request):
    total_bookings = Booking.objects.count()
    avg_adr = Booking.objects.aggregate(avg=Avg('adr'))['avg'] or 0
    avg_room_occupy = (Booking.objects
                       .annotate(total_nights=F('stays_in_weekend_nights') + F('stays_in_week_nights'))
                       .aggregate(avg_total=Avg('total_nights'))['avg_total'] or 0)

    raw = (Booking.objects
           .values('arrival_date_year', 'arrival_date_month_number')
           .annotate(c=Count('id'))
           .order_by('arrival_date_year', 'arrival_date_month_number'))

    labels = []
    data = []
    for r in raw:
        count = r['c']
        if count <= 0:
            continue
        m_abbr = calendar.month_abbr[r['arrival_date_month_number']]
        labels.append(f"{m_abbr} {r['arrival_date_year']}")
        data.append(count)

    context = {
        'total_bookings': total_bookings,
        'avg_adr': round(avg_adr, 2),
        'avg_room_occupy': round(avg_room_occupy, 2),
        'chart_labels_json': json.dumps(labels),
        'chart_data_json': json.dumps(data),
    }
    return render(request, 'dashboard/index.html', context)
