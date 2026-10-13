from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register('menu', views.MenuViewSet)
router.register('booking/tables', views.BookingViewSet)

urlpatterns = [
    path('', views.index, name='index'),
    path('api-token-auth/', obtain_auth_token),
    path('', include(router.urls)),
]
