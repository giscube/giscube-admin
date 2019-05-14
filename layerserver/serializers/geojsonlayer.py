from rest_framework import serializers

from layerserver.models import GeoJsonLayer


class GeoJSONLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoJsonLayer
        fields = ['name', 'title']
