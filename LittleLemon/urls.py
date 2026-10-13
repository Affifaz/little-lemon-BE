"""
URL configuration for LittleLemon project.
"""
from django.contrib import admin
from django.urls import include, path

from LittleLemonAPI.views import index

urlpatterns = [
    path('', index, name='index'),
    path('admin/', admin.site.urls),
    path('api/', include('LittleLemonAPI.urls')),
    # Djoser: /api/users/, /api/users/me/, /token/login/, /token/logout/
    path('api/', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
    path('api/', include('djoser.urls.authtoken')),
    # Login/logout for the browsable API
    path('api-auth/', include('rest_framework.urls')),
]
