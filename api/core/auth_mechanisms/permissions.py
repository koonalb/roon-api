"""
Rest Framework Override of permissions.

Used in permission_classes decorator
"""
from rest_framework.permissions import BasePermission


class IsSuperuser(BasePermission):
    """
    Allows access only to Superusers.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_superuser
