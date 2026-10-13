from django.core.validators import MinValueValidator
from django.db import models


class Menu(models.Model):
    title = models.CharField(max_length=255)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    inventory = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.title} : {self.price}'


class Booking(models.Model):
    name = models.CharField(max_length=255)
    no_of_guests = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    booking_date = models.DateTimeField()

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.name} - {self.no_of_guests} guests on {self.booking_date:%Y-%m-%d %H:%M}'
