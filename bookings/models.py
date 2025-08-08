from django.db import models

# Create your models here.

MONTH_CHOICES = [
    ("January", "January"),
    ("February", "February"),
    ("March", "March"),
    ("April", "April"),
    ("May", "May"),
    ("June", "June"),
    ("July", "July"),
    ("August", "August"),
    ("September", "September"),
    ("October", "October"),
    ("November", "November"),
    ("December", "December"),
]

CUSTOMER_TYPE_CHOICES = [
    ("Contract", "Contract"),
    ("Group", "Group"),
    ("Transient", "Transient"),
    ("Transient-party", "Transient-Party"),
]

DEPOSIT_TYPE_CHOICES = [
    ("No Deposit", "No Deposit"),
    ("Non Refund", "Non Refund"),
    ("Refundable", "Refundable"),
]

DISTRIBUTION_CHANNEL_CHOICES = [
    ('Direct', 'Direct'),
    ('Corporate', 'Corporate'),
    ('TA/TO', 'TA/TO'),
    ('Undefined', 'Undefined'),
]

MARKET_SEGMENT_CHOICES = [
    ("Online TA", "Online TA"),
    ("Offline TA/TO", "Offline TA/TO"),
    ("Direct", "Direct"),
    ("Groups", "Groups"),
    ("Corporate", "Corporate"),
    ("Complementary", "Complementary"),
]

MEAL_CHOICES = [
    ("Undefined", "No Meal Package"),
    ("SC", "No Meal Package"),
    ("BB", "Bed & Breakfast"),
    ("HB", "Half board"),
    ("FB", "Full board")
]

RESERVATION_STATUS_CHOICES = [
    ("Check-Out", "Check-Out"),
    ("Canceled", "Canceled"),
    ("No-Show", "Undefined")
]


class Booking(models.Model):
    is_cancelled = models.BooleanField()
    lead_time = models.IntegerField()
    arrival_date_year = models.IntegerField()
    arrival_date_month = models.CharField(max_length=20, choices=MONTH_CHOICES)
    arrival_date_week_number = models.IntegerField()
    arrival_date_day_of_month = models.IntegerField()
    stays_in_weekend_nights = models.IntegerField()
    stays_in_week_nights = models.IntegerField()
    adults = models.IntegerField()
    children = models.IntegerField()
    babies = models.IntegerField()
    meal = models.CharField(max_length=9, choices=MEAL_CHOICES)
    country = models.CharField(max_length=5)
    market_segment = models.CharField(max_length=13, choices=MARKET_SEGMENT_CHOICES)
    distribution_channel = models.CharField(max_length=9, choices=DISTRIBUTION_CHANNEL_CHOICES)
    is_repeated_guest = models.BooleanField()
    previous_cancellations = models.IntegerField()
    previous_booking_not_canceled = models.IntegerField()
    reserved_room_type = models.CharField(max_length=1)
    assigned_room_type = models.CharField(max_length=1)
    booking_changes = models.IntegerField()
    deposit_type = models.CharField(max_length=10, choices=DEPOSIT_TYPE_CHOICES)
    agent = models.IntegerField(blank=True, null=True)
    company = models.IntegerField(blank=True, null=True)
    days_in_waiting_list = models.IntegerField()
    customer_type = models.CharField(max_length=15, choices=CUSTOMER_TYPE_CHOICES)
    adr = models.FloatField()
    required_card_parking_spaces = models.IntegerField()
    total_of_special_requests = models.IntegerField()
    reservation_status = models.CharField(max_length=9, choices=RESERVATION_STATUS_CHOICES)
    reservation_status_date = models.DateField()
    id = models.BigAutoField(primary_key=True)
