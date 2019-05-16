from rest_framework import serializers

from layerserver.models import DataBaseLayerField
from layerserver.widgets import widgets_types


class DBLayerVirtualFieldListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        data = data.filter(enabled=True)
        return super().to_representation(data)


class DBLayerVirtualFieldSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        data = super().to_representation(obj)
        data['widget'] = obj.widget
        data.update(widgets_types[obj.widget].serialize_widget_options(obj))
        return data

    class Meta:
        model = DataBaseLayerField
        fields = ['name', 'label']
        list_serializer_class = DBLayerVirtualFieldListSerializer
