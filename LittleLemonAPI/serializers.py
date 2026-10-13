from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Booking, Cart, Category, MenuItem, Order, OrderItem
from .permissions import DELIVERY_CREW_GROUP


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'slug', 'title']


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'category', 'featured']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['id', 'menuitem', 'quantity', 'unit_price', 'price']
        read_only_fields = ['unit_price', 'price']


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'menuitem', 'quantity', 'unit_price', 'price']


class OrderSerializer(serializers.ModelSerializer):
    delivery_crew = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(groups__name=DELIVERY_CREW_GROUP),
        allow_null=True, required=False,
    )
    order_items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew', 'status', 'total', 'date', 'order_items']
        read_only_fields = ['user', 'total', 'date']


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'user', 'name', 'no_of_guests', 'booking_date']
        read_only_fields = ['user']
