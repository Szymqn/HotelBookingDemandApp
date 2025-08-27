import django_tables2 as tables
from django.utils.html import format_html
from .models import Booking


class BookingTable(tables.Table):
    stay_nights = tables.Column(verbose_name="Nights", empty_values=(), orderable=False)
    is_cancelled = tables.Column(verbose_name="Cancelled", attrs={"td": {"class": "text-center"}})
    lead_time = tables.Column(attrs={"td": {"class": "text-end"}})
    adults = tables.Column(attrs={"td": {"class": "text-end"}})
    children = tables.Column(attrs={"td": {"class": "text-end"}})
    babies = tables.Column(attrs={"td": {"class": "text-end"}})
    adr = tables.Column(verbose_name="ADR ($)", attrs={"td": {"class": "text-end"}})

    class Meta:
        model = Booking
        template_name = "django_tables2/bootstrap5.html"
        order_by = ("-arrival_date",)
        fields = (
            "arrival_date",
            "hotel",
            "is_cancelled",
            "stay_nights",
            "lead_time",
            "adults",
            "children",
            "babies",
            "adr",
            "country",
            "market_segment",
            "distribution_channel",
            "reserved_room_type",
            "assigned_room_type",
            "deposit_type",
            "customer_type",
            "reservation_status",
        )
        attrs = {
            "class": "table table-sm table-striped table-hover align-middle table-bordered text-nowrap",
            "thead": {"class": "table-light sticky-top"},
        }

    def render_stay_nights(self, record):
        return (record.stays_in_week_nights or 0) + (record.stays_in_weekend_nights or 0)

    def render_is_cancelled(self, value):
        badge = "bg-danger" if value else "bg-success"
        text = "Yes" if value else "No"
        return format_html('<span class="badge {}">{}</span>', badge, text)

    def render_adr(self, value):
        if value is None:
            return "-"
        return f"{value:,.2f}"
