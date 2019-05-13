from django.contrib.auth.models import AnonymousUser

from rest_framework import permissions

from .models import DataBaseLayer, DBLayerGroup


class DBLayerPermissions():
    @staticmethod
    def get_permissions(layer, user):
        permission = {
            'view': False,
            'add': False,
            'update': False,
            'delete': False
        }

        if type(user) == AnonymousUser:
            permission['view'] = layer.anonymous_view
            permission['add'] = layer.anonymous_add
            permission['update'] = layer.anonymous_update
            permission['delete'] = layer.anonymous_delete
            return permission
        else:
            permission['view'] = layer.anonymous_view
            permission['add'] = layer.anonymous_add
            permission['update'] = layer.anonymous_update
            permission['delete'] = layer.anonymous_delete

        p = layer.layer_users.filter(user=user).first()
        if p:
            if p.can_view:
                permission['view'] = p.can_view
            if p.can_add:
                permission['add'] = p.can_add
            if p.can_update:
                permission['update'] = p.can_update
            if p.can_delete:
                permission['delete'] = p.can_delete
        else:
            ps = DBLayerGroup.objects.filter(layer=layer, group__in=user.groups.all())
            for p in ps:
                if p.can_view:
                    permission['view'] = p.can_view
                if p.can_add:
                    permission['add'] = p.can_add
                if p.can_update:
                    permission['update'] = p.can_update
                if p.can_delete:
                    permission['delete'] = p.can_delete

        return permission


class DBLayerIsValidUser(permissions.BasePermission, DBLayerPermissions):
    def has_permission(self, request, view):
        permission = self.get_permissions(view.layer, request.user)
        permissions = []

        if permission['view']:
            permissions.append('get')
            permissions.append('options')
        if permission['add']:
            permissions.append('post')
        if permission['update']:
            permissions.append('put')
            permissions.append('patch')
        if permission['delete']:
            permissions.append('delete')

        if request.method.lower() in permissions:
            return True
        else:
            return False


class BulkDBLayerIsValidUser(permissions.BasePermission, DBLayerPermissions):
    def has_permission(self, request, view):
        permission = self.get_permissions(view.layer, request.user)
        return permission['add'] and permission['update'] and permission['delete']


class DataBaseLayerDjangoPermission(permissions.DjangoModelPermissions):
    """
    Check if user has permission on DataBaseLayer Model
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

    def get_required_permissions(self, method, model_cls):
        model_cls = DataBaseLayer
        return super().get_required_permissions(method, model_cls)

    def has_permission(self, request, view):
        # Workaround to ensure DjangoModelPermissions are not applied
        # to the root view when using DefaultRouter.
        if getattr(view, '_ignore_model_permissions', False):
            return True

        if not request.user or (
           not request.user.is_authenticated and self.authenticated_users_only):
            return False

        perms = self.get_required_permissions(request.method, DataBaseLayer)
        return request.user.has_perms(perms)
