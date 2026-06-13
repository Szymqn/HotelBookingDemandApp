import django_tables2 as tables
from django.utils.html import format_html
from .models import Booking


class BookingTable(tables.Table):
    hotel = tables.Column(attrs={"th": {"class": "ps-4"}, "td": {"class": "ps-4 fw-medium text-body"}})
    arrival_date = tables.Column(verbose_name="Arrival", attrs={"td": {"class": "text-secondary"}})
    is_cancelled = tables.Column(verbose_name="Status", attrs={"th": {"class": "text-center"}, "td": {"class": "text-center"}})
    stay_nights = tables.Column(verbose_name="Nights", empty_values=(), orderable=False, attrs={"th": {"class": "text-center"}, "td": {"class": "text-center"}})
    lead_time = tables.Column(verbose_name="Lead Days", attrs={"th": {"class": "text-end"}, "td": {"class": "text-end text-secondary"}})
    adults = tables.Column(attrs={"th": {"class": "text-center"}, "td": {"class": "text-center"}})
    children = tables.Column(attrs={"th": {"class": "text-center"}, "td": {"class": "text-center"}})
    babies = tables.Column(attrs={"th": {"class": "text-center"}, "td": {"class": "text-center"}})
    adr = tables.Column(verbose_name="ADR", attrs={"th": {"class": "text-end"}, "td": {"class": "text-end fw-medium"}})
    country = tables.Column(attrs={"td": {"class": "text-secondary"}})
    market_segment = tables.Column(verbose_name="Market", attrs={"td": {"class": "text-secondary"}})
    distribution_channel = tables.Column(verbose_name="Channel", attrs={"td": {"class": "text-secondary"}})
    reserved_room_type = tables.Column(verbose_name="Room", attrs={"th": {"class": "text-center"}, "td": {"class": "text-center fw-medium"}})
    deposit_type = tables.Column(verbose_name="Deposit", attrs={"td": {"class": "text-secondary"}})
    customer_type = tables.Column(verbose_name="Customer", attrs={"td": {"class": "text-secondary"}})
    reservation_status = tables.Column(verbose_name="Details", attrs={"td": {"class": "text-secondary pe-4"}, "th": {"class": "pe-4"}})

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
            "deposit_type",
            "customer_type",
            "reservation_status",
        )
        attrs = {
            "class": "table table-hover align-middle mb-0 text-nowrap",
            "thead": {"class": "sticky-top"},
        }

    def render_stay_nights(self, record):
        return (record.stays_in_week_nights or 0) + (record.stays_in_weekend_nights or 0)

    def render_is_cancelled(self, value):
        badge = "bg-danger-subtle text-danger" if value else "bg-success-subtle text-success"
        text = "Cancelled" if value else "Confirmed"
        return format_html('<span class="badge {} rounded-pill fw-medium border border-1" style="font-size: 0.75rem;">{}</span>', badge, text)

    def render_adr(self, value):
        if value is None:
            return "-"
        return f"${value:,.2f}"
