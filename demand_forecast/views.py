import calendar
import json

from django.db.models import Count
from django.shortcuts import render

from bookings.models import Booking


# Create your views here.
def index(request):
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
        'chart_labels_json': json.dumps(labels),
        'chart_data_json': json.dumps(data),
    }

    return render(request, "demand_forecast/index.html", context)
