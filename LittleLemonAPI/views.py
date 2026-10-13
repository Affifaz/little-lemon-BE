from django.contrib.auth.models import Group, User
from django.db import transaction
from django.shortcuts import get_object_or_404, render
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Booking, Cart, Category, MenuItem, Order, OrderItem
from .permissions import (
    IsManager, IsManagerOrReadOnly, is_delivery_crew, is_manager,
)
from .serializers import (
    BookingSerializer, CartSerializer, CategorySerializer, MenuItemSerializer, OrderSerializer,
    UserSerializer,
)


def index(request):
    return render(request, 'index.html')


class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsManagerOrReadOnly]
    pagination_class = None
    search_fields = ['title']
    ordering_fields = ['title']


class SingleCategoryView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsManagerOrReadOnly]


class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.select_related('category')
    serializer_class = MenuItemSerializer
    permission_classes = [IsManagerOrReadOnly]
    filterset_fields = ['category', 'category__slug', 'category__title', 'featured']
    ordering_fields = ['price', 'title']
    search_fields = ['title', 'category__title']


class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.select_related('category')
    serializer_class = MenuItemSerializer
    permission_classes = [IsManagerOrReadOnly]


class GroupUsersView(APIView):
    """List the users of a group, or add the user named in the payload to it."""
    permission_classes = [IsManager]
    group_name = None
    group_label = None

    def get_group(self):
        return Group.objects.get_or_create(name=self.group_name)[0]

    def get(self, request):
        users = self.get_group().user_set.order_by('id')
        return Response(UserSerializer(users, many=True).data)

    def post(self, request):
        username = request.data.get('username')
        if not username:
            return Response(
                {'username': ['This field is required.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = get_object_or_404(User, username=username)
        self.get_group().user_set.add(user)
        return Response(
            {'message': f'user added to the {self.group_label} group'},
            status=status.HTTP_201_CREATED,
        )


class SingleGroupUserView(GroupUsersView):
    """Remove a user from a group."""
    http_method_names = ['delete', 'options']

    def delete(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        self.get_group().user_set.remove(user)
        return Response({'message': f'user removed from the {self.group_label} group'})


class CartView(generics.ListCreateAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        menuitem = serializer.validated_data['menuitem']
        quantity = serializer.validated_data['quantity']

        # Adding an item that is already in the cart increases its quantity
        cart_item, created = Cart.objects.get_or_create(
            user=request.user, menuitem=menuitem,
            defaults={
                'quantity': quantity,
                'unit_price': menuitem.price,
                'price': menuitem.price * quantity,
            },
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.unit_price = menuitem.price
            cart_item.price = menuitem.price * cart_item.quantity
            cart_item.save()
        return Response(self.get_serializer(cart_item).data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        self.get_queryset().delete()
        return Response({'message': 'cart emptied'})


class OrderQuerysetMixin:
    """Managers see every order, delivery crew the orders assigned to them,
    customers only their own."""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        orders = Order.objects.prefetch_related('order_items')
        if is_manager(user):
            return orders
        if is_delivery_crew(user):
            return orders.filter(delivery_crew=user)
        return orders.filter(user=user)


class OrdersView(OrderQuerysetMixin, generics.ListCreateAPIView):
    filterset_fields = ['status', 'delivery_crew', 'date']
    ordering_fields = ['date', 'total']

    def create(self, request, *args, **kwargs):
        """Turn the current user's cart into an order and empty the cart."""
        with transaction.atomic():
            cart_items = list(Cart.objects.filter(user=request.user))
            if not cart_items:
                return Response(
                    {'message': 'your cart is empty'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            order = Order.objects.create(
                user=request.user,
                total=sum(item.price for item in cart_items),
            )
            OrderItem.objects.bulk_create([
                OrderItem(
                    order=order, menuitem_id=item.menuitem_id,
                    quantity=item.quantity, unit_price=item.unit_price,
                    price=item.price,
                )
                for item in cart_items
            ])
            Cart.objects.filter(user=request.user).delete()
        return Response(self.get_serializer(order).data, status=status.HTTP_201_CREATED)


class SingleOrderView(OrderQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    def update(self, request, *args, **kwargs):
        user = request.user
        if is_manager(user):
            return super().update(request, *args, **kwargs)
        # Delivery crew may only mark an order as delivered or not
        if (
            is_delivery_crew(user)
            and kwargs.get('partial')
            and set(request.data.keys()) == {'status'}
        ):
            return super().update(request, *args, **kwargs)
        raise PermissionDenied()

    def destroy(self, request, *args, **kwargs):
        if not is_manager(request.user):
            raise PermissionDenied()
        return super().destroy(request, *args, **kwargs)


class BookingQuerysetMixin:
    """Managers see every table booking, everyone else only their own."""
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if is_manager(user):
            return Booking.objects.all()
        return Booking.objects.filter(user=user)


class BookingsView(BookingQuerysetMixin, generics.ListCreateAPIView):
    filterset_fields = ['booking_date', 'no_of_guests']
    ordering_fields = ['booking_date', 'no_of_guests']
    search_fields = ['name']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SingleBookingView(BookingQuerysetMixin, generics.RetrieveUpdateDestroyAPIView):
    pass
