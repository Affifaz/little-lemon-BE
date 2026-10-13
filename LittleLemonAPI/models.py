from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=255, db_index=True)

    class Meta:
        ordering = ['id']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.title


class MenuItem(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    price = models.DecimalField(
        max_digits=6, decimal_places=2, db_index=True,
        validators=[MinValueValidator(0)],
    )
    featured = models.BooleanField(db_index=True, default=False)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.title


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['menuitem', 'user'], name='unique_cart_menuitem_user'),
        ]

    def __str__(self):
        return f'{self.user} - {self.menuitem} x {self.quantity}'


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    delivery_crew = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name='deliveries',
        null=True, blank=True,
    )
    # False = out for delivery, True = delivered
    status = models.BooleanField(db_index=True, default=False)
    total = models.DecimalField(max_digits=8, decimal_places=2)
    date = models.DateField(db_index=True, auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'Order {self.pk} ({self.user})'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    menuitem = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'menuitem'], name='unique_order_menuitem'),
        ]

    def __str__(self):
        return f'{self.order} - {self.menuitem} x {self.quantity}'


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    name = models.CharField(max_length=255)
    no_of_guests = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    booking_date = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.name} - {self.no_of_guests} guests on {self.booking_date:%Y-%m-%d %H:%M}'
