from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Booking, Menu
from .permissions import IsStaffOrReadOnly
from .serializers import BookingSerializer, MenuSerializer


def index(request):
    return render(request, 'index.html', {})


class MenuViewSet(viewsets.ModelViewSet):
    """Anyone can browse the menu; only staff can change it."""
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer
    permission_classes = [IsStaffOrReadOnly]


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
