from django.db.models import Q

from rest_framework import permissions


class PermissionNone(permissions.BasePermission):
    """
    No permission
    """

    def has_permission(self, request, view):
        return False


class FixedDjangoModelPermissions(permissions.DjangoModelPermissions):
    """
    Overwrite DjangoModelPermissions to avoid GET
    """
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


class PermissionQuerysetMixin:
    def get_queryset(self, *args, **kwargs):
        qs = self.model.objects.filter(active=True)
        filter_anonymous = Q(anonymous_view=True)

        if self.request.user.is_anonymous:
            qs = qs.filter(filter_anonymous)
        else:
            self.user_groups = self.request.user.groups.values_list('name', flat=True)
            filter_authenticated_user_view = Q(authenticated_user_view=True)
            filter_group = (
                Q(group_permissions__group__name__in=self.user_groups) & Q(group_permissions__can_view=True))
            filter_user = Q(user_permissions__user=self.request.user) & Q(
                user_permissions__can_view=True)
            qs = qs.filter(
                filter_anonymous | filter_authenticated_user_view | filter_user | filter_group).distinct()

        return qs

    def get_queryset_can_write(self, *args, **kwargs):
        qs = self.model.objects.filter(active=True)
        filter_anonymous = Q(anonymous_write=True)

        if self.request.user.is_anonymous:
            qs = qs.filter(filter_anonymous)
        else:
            self.user_groups = self.request.user.groups.values_list('name', flat=True)
            filter_authenticated_user_write = Q(authenticated_user_write=True)
            filter_group = (
                Q(group_permissions__group__name__in=self.user_groups) & Q(group_permissions__can_write=True))
            filter_user = Q(user_permissions__user=self.request.user) & Q(
                user_permissions__can_write=True)
            qs = qs.filter(
                filter_anonymous | filter_authenticated_user_write | filter_user | filter_group).distinct()

        return qs
