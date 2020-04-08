class PermissionIndexMixin(object):
    def prepare_search_data(self, obj):
        data = super().prepare_search_data(obj)
        permissions = {'user': {}, 'group': {}}

        if obj.anonymous_view:
            permissions['user'][''] = 'v'

        if hasattr(obj, 'authenticated_user_view') and obj.authenticated_user_view:
            permissions['authenticated_user'] = 'v'

        for permission in obj.user_permissions.filter(can_view=True).select_related('user'):
            permissions['user'][permission.user.username] = 'v'

        for permission in obj.group_permissions.filter(can_view=True).select_related('group'):
            permissions['group'][permission.group.name] = 'v'

        if len(list(permissions.keys())) > 0:
            data['permissions'] = permissions
        return data


class VisibilityIndexMixin(object):
    def prepare_search_data(self, obj):
        data = super().prepare_search_data(obj)
        if obj.visibility == 'public':
            data['permissions'] = {'user': {'': 'v'}}
        else:
            data['permissions'] = {'authenticated_user': 'v'}
        return data
