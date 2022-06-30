from rest_framework import serializers

from layerserver.models import GeoJsonFilter


class GeoJSONFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoJsonFilter
        fields = ['title', 'description', 'filter']
