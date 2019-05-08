from rest_framework import serializers

from .models import DataBaseLayerField
from .widgets import widgets_types


class DBLayerFieldListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        data = data.filter(enabled=True)
        return super(
            DBLayerFieldListSerializer, self).to_representation(data)


class DBLayerFieldSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        data = super(
            DBLayerFieldSerializer, self).to_representation(obj)

        data['null'] = obj.null
        data['blank'] = obj.blank
        data['size'] = obj.size
        data['decimals'] = obj.decimals
        data['widget'] = obj.widget
        data.update(widgets_types[obj.widget].serialize_widget_options(obj))
        return data

    class Meta:
        model = DataBaseLayerField
        fields = ['name', 'label', 'search', 'fullsearch', 'readonly']
        list_serializer_class = DBLayerFieldListSerializer
