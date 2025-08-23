import csv
import calendar

from django.core.management.base import BaseCommand
from datetime import datetime, date
from bookings.models import Booking


class Command(BaseCommand):
    help = 'Import bookings from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']

        def clean_value(value):
            if value is None:
                return None
            value = value.strip()
            if value.upper() == "NULL" or value == "":
                return None
            return value

        with open(csv_file_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            bookings = []
            for row in reader:
                row = [clean_value(col) for col in row]

                year = int(row[3])
                month_num = list(calendar.month_name).index(row[4])
                day = int(row[6])

                try:
                    full_arrival_date = date(year, month_num, day)
                except ValueError:
                    full_arrival_date = None

                booking = Booking(
                    hotel=row[0],
                    is_cancelled=bool(int(row[1])),
                    lead_time=int(row[2]),
                    arrival_date_year=year,
                    arrival_date_month=row[4],
                    arrival_date_week_number=int(row[5]),
                    arrival_date_month_number=month_num,
                    arrival_date_day_of_month=day,
                    arrival_date=full_arrival_date,
                    stays_in_weekend_nights=int(row[7]),
                    stays_in_week_nights=int(row[8]),
                    adults=int(row[9]),
                    children=int(row[10]) if row[10] is not None and row[10].isdigit() else None,
                    babies=int(row[11]),
                    meal=row[12],
                    country=row[13],
                    market_segment=row[14],
                    distribution_channel=row[15],
                    is_repeated_guest=bool(int(row[16])),
                    previous_cancellations=int(row[17]),
                    previous_booking_not_canceled=int(row[18]),
                    reserved_room_type=row[19],
                    assigned_room_type=row[20],
                    booking_changes=int(row[21]),
                    deposit_type=row[22],
                    agent=int(row[23]) if row[23] is not None else None,
                    company=int(row[24]) if row[24] is not None else None,
                    days_in_waiting_list=int(row[25]),
                    customer_type=row[26],
                    adr=float(row[27]),
                    required_card_parking_spaces=int(row[28]),
                    total_of_special_requests=int(row[29]),
                    reservation_status=row[30],
                    reservation_status_date=datetime.strptime(row[31], "%Y-%m-%d").date()
                )
                bookings.append(booking)

            Booking.objects.bulk_create(bookings)
            self.stdout.write(self.style.SUCCESS(f"Imported {len(bookings)} bookings"))
