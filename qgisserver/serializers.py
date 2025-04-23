import base64

from django.core.files.base import ContentFile
from django.db import transaction

from rest_framework import serializers

from .models import Group, Project, Service, ServiceFilter, ServiceGroupPermission, ServiceUserPermission, User


class Base64Field(serializers.FileField):
    # https://en.wikipedia.org/wiki/Data_URI_scheme#Syntax
    # data:[<media type>][;charset=<character set>][;base64],<data>
    def to_internal_value(self, data):
        try:
            parts = data.split(';base64,')
            decoded_file = base64.b64decode(parts[1])
            file_name = [x for x in parts[0].split(';') if x.lower().startswith('name=')][0].split('=')[1]
        except Exception:
            raise serializers.ValidationError('invalid_file')

        data = ContentFile(decoded_file, name=file_name)

        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        if not self.instance and 'username' in data and data['username']:
            self.instance = User.objects.filter(username=data['username']).first()
        return super().to_internal_value(data)

    class Meta:
        model = User
        fields = ('username', 'email')


class ServiceUserPermissionSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = ServiceUserPermission
        fields = ('user', 'can_view', 'can_write')


class GroupSerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        if not self.instance and 'name' in data and data['name']:
            self.instance = Group.objects.filter(name=data['name']).first()
        return super().to_internal_value(data)

    class Meta:
        model = Group
        fields = ('name',)


class ServiceGroupPermissionSerializer(serializers.ModelSerializer):
    group = GroupSerializer()

    class Meta:
        model = ServiceGroupPermission
        fields = ('group', 'can_view', 'can_write')


class ServiceFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceFilter
        fields = '__all__'


class ServiceSerializer(serializers.ModelSerializer):
    user_permissions = ServiceUserPermissionSerializer(many=True)
    group_permissions = ServiceGroupPermissionSerializer(many=True)
    service_filter = ServiceFilterSerializer(many=True, required=False)
    project_file = Base64Field()

    @transaction.atomic
    def create(self, validated_data):
        user_permissions = validated_data.pop('user_permissions', [])
        group_permissions = validated_data.pop('group_permissions', [])
        service = super().create(validated_data)
        for permission in user_permissions:
            permission_user = permission['user']
            user, _ = User.objects.get_or_create(
                username=permission_user['username'],
                defaults={'email': permission_user['email']}
            )
            ServiceUserPermission.objects.create(
                service=service,
                user=user,
                can_view=permission['can_view'],
                can_write=permission['can_write']
            )
        for permission in group_permissions:
            group, _ = Group.objects.get_or_create(
                name=permission['group']['name']
            )
            ServiceGroupPermission.objects.create(
                service=service, group=group, can_view=permission['can_view'])

        return service

    @transaction.atomic
    def update(self, instance, validated_data):
        user_permissions = validated_data.pop('user_permissions', [])
        group_permissions = validated_data.pop('group_permissions', [])
        usernames = []
        for permission in user_permissions:
            permission_user = permission['user']
            user, _ = User.objects.update_or_create(
                username=permission_user['username'],
                defaults={'email': permission_user['email']}
            )
            usernames.append(user.username)
            ServiceUserPermission.objects.update_or_create(
                service=instance,
                user=user,
                defaults={'can_view': permission['can_view'], 'can_write': permission['can_write']}
            )

        group_names = []
        for permission in group_permissions:
            group, _ = Group.objects.get_or_create(
                name=permission['group']['name']
            )
            group_names.append(group.name)
            ServiceGroupPermission.objects.update_or_create(
                service=instance,
                group=group,
                defaults={'can_view': permission['can_view'], 'can_write': permission['can_write']}
            )
        instance.user_permissions.exclude(user__username__in=(usernames)).delete()
        instance.group_permissions.exclude(group__name__in=(group_names)).delete()
        return super().update(instance, validated_data)

    class Meta:
        model = Service
        fields = (
            'id',
            'name',
            'title',
            'description',
            'keywords',
            'active',
            'visible_on_geoportal',
            'category',
            'project_file',
            'user_permissions',
            'group_permissions',
            'service_filter'
        )


class ProjectSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ('id', 'name', 'data', 'service')
