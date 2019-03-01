from __future__ import unicode_literals

from rest_framework import serializers

from .models import Category, UserAsset


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'parent')


class UserAssetSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        data = super(
            UserAssetSerializer, self).to_representation(obj)
        data['url'] = data['file']
        data['file'] = r'media://%s' % obj.file.name
        return data

    class Meta:
        model = UserAsset
        fields = ('uuid', 'file', 'created')
        read_only_fields = ('uuid', 'created')
