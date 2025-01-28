from urllib.parse import urljoin

from django.conf import settings

from giscube.utils import url_slash_join

from rest_framework import serializers

from .models import Category, MapConfig, MapConfigBaseLayer, UserAsset


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'parent')


class UserAssetSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        token = None
        auth = getattr(self.context['request'], 'auth', None)
        if hasattr(auth, 'token'):
            token = self.context['request'].auth.token
        data = super(
            UserAssetSerializer, self).to_representation(obj)
        media_url = urljoin(settings.GISCUBE_URL, settings.MEDIA_URL)
        data["url"] = url_slash_join(media_url, obj.file.name)
        if token:
            data['url'] = '%s?access_token=%s' % (data['url'], token)
        data['file'] = r'media://%s' % obj.file.name
        return data

    class Meta:
        model = UserAsset
        fields = ('uuid', 'file', 'created')
        read_only_fields = ('uuid', 'created')


class MapConfigBaseLayerSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='base_layer.id')
    name = serializers.ReadOnlyField(source='base_layer.name')
    properties = serializers.ReadOnlyField(source='base_layer.properties')

    class Meta:
        model = MapConfigBaseLayer
        fields = ('id', 'order', 'name', 'properties')


class MapConfigSerializer(serializers.ModelSerializer):
    baselayers = MapConfigBaseLayerSerializer(read_only=True, many=True)

    class Meta:
        model = MapConfig
        fields = ('id', 'name', 'center_lat', 'center_lng', 'initial_zoom', 'baselayers')
