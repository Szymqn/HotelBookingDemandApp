import calendar
import json

from django.db.models import Avg, Count, ExpressionWrapper, F, FloatField
from django.shortcuts import render

from bookings.models import Booking


def _get_month_over_month():
    raw = list(
        Booking.objects.values("arrival_date_year", "arrival_date_month_number")
        .annotate(
            bookings=Count("id"),
            avg_adr=Avg("adr"),
            avg_nights=Avg(
                ExpressionWrapper(
                    F("stays_in_weekend_nights") + F("stays_in_week_nights"),
                    output_field=FloatField(),
                )
            ),
        )
        .order_by("arrival_date_year", "arrival_date_month_number")
    )
    if len(raw) < 2:
        return None, None, None

    prev, curr = raw[-2], raw[-1]

    def pct(new, old):
        if not old:
            return None
        return round((new - old) / old * 100, 1)

    return (
        pct(curr["bookings"], prev["bookings"]),
        pct(curr["avg_adr"], prev["avg_adr"]),
        pct(curr["avg_nights"], prev["avg_nights"]),
    )


def _get_ai_insights():
    total = Booking.objects.count()
    if not total:
        return []

    insights = []

    # Peak demand month
    peak = (
        Booking.objects.values("arrival_date_month", "arrival_date_month_number")
        .annotate(bookings=Count("id"))
        .order_by("-bookings")
        .first()
    )
    if peak:
        avg_per_month = total / 12
        pct_above = round((peak["bookings"] - avg_per_month) / avg_per_month * 100)
        insights.append(
            {
                "icon": "trending_up",
                "icon_color": "text-primary",
                "title": f"Peak Season: {peak['arrival_date_month']}",
                "text": (
                    f"{peak['arrival_date_month']} is your historically busiest month — "
                    f"{pct_above}% above the monthly average. Consider rate adjustments for this period."
                ),
            }
        )

    # Cancellation rate + non-refundable risk
    cancelled = Booking.objects.filter(is_cancelled=True).count()
    cancel_rate = round(cancelled / total * 100, 1)
    nonrefund_active = Booking.objects.filter(
        is_cancelled=False, deposit_type="Non Refund"
    ).count()
    insights.append(
        {
            "icon": "warning",
            "icon_color": "text-warning",
            "title": "Cancellation Risk",
            "text": (
                f"{cancel_rate}% of all bookings were cancelled. "
                f"{nonrefund_active} active non-refundable bookings show an elevated cancellation pattern."
            ),
        }
    )

    # ADR gap between hotel types
    adr_rows = list(Booking.objects.values("hotel").annotate(avg_adr=Avg("adr")))
    adr_dict = {r["hotel"]: r["avg_adr"] for r in adr_rows}
    city = adr_dict.get("City Hotel")
    resort = adr_dict.get("Resort Hotel")
    if city and resort:
        diff_pct = round(abs(city - resort) / min(city, resort) * 100, 1)
        higher = "City Hotel" if city > resort else "Resort Hotel"
        lower = "Resort Hotel" if city > resort else "City Hotel"
        insights.append(
            {
                "icon": "insights",
                "icon_color": "text-success",
                "title": "Pricing Opportunity",
                "text": (
                    f"{higher} ADR is {diff_pct}% higher than {lower} "
                    f"(${round(city, 2)} vs ${round(resort, 2)}). "
                    f"Review segment-level pricing to optimise revenue."
                ),
            }
        )

    return insights


def _trend(pct_change):
    if pct_change is None:
        return None
    return {
        "value": abs(pct_change),
        "up": pct_change >= 0,
        "label": f"+{pct_change}%" if pct_change >= 0 else f"{pct_change}%",
    }


def index(request):
    total_bookings = Booking.objects.count()
    avg_adr = Booking.objects.aggregate(avg=Avg("adr"))["avg"] or 0
    avg_room_occupy = (
        Booking.objects.annotate(
            total_nights=F("stays_in_weekend_nights") + F("stays_in_week_nights")
        ).aggregate(avg_total=Avg("total_nights"))["avg_total"]
        or 0
    )

    raw = (
        Booking.objects.values("arrival_date_year", "arrival_date_month_number")
        .annotate(c=Count("id"))
        .order_by("arrival_date_year", "arrival_date_month_number")
    )
    labels, data = [], []
    for r in raw:
        if r["c"] <= 0:
            continue
        labels.append(
            f"{calendar.month_abbr[r['arrival_date_month_number']]} {r['arrival_date_year']}"
        )
        data.append(r["c"])

    b_chg, adr_chg, occ_chg = _get_month_over_month()

    context = {
        "total_bookings": total_bookings,
        "avg_adr": round(avg_adr, 2),
        "avg_room_occupy": round(avg_room_occupy, 2),
        "bookings_trend": _trend(b_chg),
        "adr_trend": _trend(adr_chg),
        "occupancy_trend": _trend(occ_chg),
        "ai_insights": _get_ai_insights(),
        "chart_labels_json": json.dumps(labels),
        "chart_data_json": json.dumps(data),
    }
    return render(request, "dashboard/index.html", context)
