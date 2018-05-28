# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import permissions

from django.contrib.auth.models import AnonymousUser

from .models import DBLayerGroup


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

        layer_user = layer.layer_users.filter(user=user).first()
        if layer_user:
            permission['view'] = layer_user.can_view
            permission['add'] = layer_user.can_add
            permission['update'] = layer_user.can_update
            permission['delete'] = layer_user.can_delete
        else:
            ps = DBLayerGroup.objects.filter(
                layer=layer,
                group__in=user.groups.all(),
                )
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
