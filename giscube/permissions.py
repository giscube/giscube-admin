from rest_framework import permissions


class PermissionNone(permissions.BasePermission):
    """
    No permission
    """

    def has_permission(self, request, view):
        return False
