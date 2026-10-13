"""
URL configuration for littlelemon project.
"""
from django.contrib import admin
from django.urls import include, path

from restaurant.views import index

urlpatterns = [
    path('', index, name='home'),
    path('admin/', admin.site.urls),
    path('restaurant/', include('restaurant.urls')),
    # Djoser: /auth/users/, /auth/users/me/, /auth/token/login/, /auth/token/logout/
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    # Login/logout for the browsable API
    path('api-auth/', include('rest_framework.urls')),
]
