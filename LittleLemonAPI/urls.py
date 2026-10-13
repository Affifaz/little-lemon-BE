from django.urls import re_path

from . import views
from .permissions import DELIVERY_CREW_GROUP, MANAGER_GROUP

manager = {'group_name': MANAGER_GROUP, 'group_label': 'manager'}
delivery_crew = {'group_name': DELIVERY_CREW_GROUP, 'group_label': 'delivery crew'}

# The trailing slash is optional on every endpoint
urlpatterns = [
    re_path(r'^categories/?$', views.CategoriesView.as_view()),
    re_path(r'^categories/(?P<pk>\d+)/?$', views.SingleCategoryView.as_view()),
    re_path(r'^menu-items/?$', views.MenuItemsView.as_view()),
    re_path(r'^menu-items/(?P<pk>\d+)/?$', views.SingleMenuItemView.as_view()),
    re_path(r'^groups/manager/users/?$', views.GroupUsersView.as_view(**manager)),
    re_path(r'^groups/manager/users/(?P<pk>\d+)/?$',
            views.SingleGroupUserView.as_view(**manager)),
    re_path(r'^groups/delivery-crew/users/?$',
            views.GroupUsersView.as_view(**delivery_crew)),
    re_path(r'^groups/delivery-crew/users/(?P<pk>\d+)/?$',
            views.SingleGroupUserView.as_view(**delivery_crew)),
    re_path(r'^cart/menu-items/?$', views.CartView.as_view()),
    re_path(r'^orders/?$', views.OrdersView.as_view()),
    re_path(r'^orders/(?P<pk>\d+)/?$', views.SingleOrderView.as_view()),
    re_path(r'^bookings/?$', views.BookingsView.as_view()),
    re_path(r'^bookings/(?P<pk>\d+)/?$', views.SingleBookingView.as_view()),
]
