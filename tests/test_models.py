from datetime import datetime, timezone

from django.core.exceptions import ValidationError
from django.test import TestCase

from restaurant.models import Booking, Menu


class MenuTest(TestCase):
    def test_get_item(self):
        item = Menu.objects.create(title='IceCream', price=80, inventory=100)
        self.assertEqual(str(item), 'IceCream : 80')

    def test_price_cannot_be_negative(self):
        item = Menu(title='IceCream', price=-1, inventory=100)
        with self.assertRaises(ValidationError):
            item.full_clean()


class BookingTest(TestCase):
    def test_get_booking(self):
        booking = Booking.objects.create(
            name='Adrian', no_of_guests=4,
            booking_date=datetime(2026, 12, 24, 19, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(str(booking), 'Adrian - 4 guests on 2026-12-24 19:00')

    def test_needs_at_least_one_guest(self):
        booking = Booking(
            name='Adrian', no_of_guests=0,
            booking_date=datetime(2026, 12, 24, 19, 0, tzinfo=timezone.utc),
        )
        with self.assertRaises(ValidationError):
            booking.full_clean()
