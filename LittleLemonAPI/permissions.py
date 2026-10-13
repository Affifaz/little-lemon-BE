from rest_framework.permissions import SAFE_METHODS, BasePermission

MANAGER_GROUP = 'Manager'
DELIVERY_CREW_GROUP = 'Delivery crew'


def is_manager(user):
    """Admins (superusers) can do everything a manager can."""
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name=MANAGER_GROUP).exists()
    )


def is_delivery_crew(user):
    return user.is_authenticated and user.groups.filter(name=DELIVERY_CREW_GROUP).exists()


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return is_manager(request.user)


class IsManagerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or is_manager(request.user)
