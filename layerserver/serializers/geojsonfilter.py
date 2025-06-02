from rest_framework import serializers

from layerserver.models import GeoJsonFilter


class GeoJSONFilterSerializer(serializers.ModelSerializer):
    color = serializers.CharField(required=False)
    icon = serializers.CharField(required=False)

    class Meta:
        model = GeoJsonFilter
        fields = ['title', 'description', 'filter', 'color', 'icon']

    def get_color(self, obj):
        return obj.fill_color if obj.fill_color else obj.stroke_color or obj.icon_color
    
    def get_icon(self, obj):
        return obj.icon
