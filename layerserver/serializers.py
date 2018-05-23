from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
import django.contrib.gis.db.models.fields
from .models import DataBaseLayer, DataBaseLayerField


def create_serializer(model, fields, id_field):
    if id_field is None or id_field == '':
        id_field = id

    geo_field = None
    for f in model._meta.fields:
        if type(f) == django.contrib.gis.db.models.fields.GeometryField:
            geo_field = str(f).split('.')[-1]
            break

    if geo_field is not None:

        if len(fields) > 0:
            attrs = {
                '__module__': 'layerserver',
                'Meta': type('Meta', (object,),
                             {'model': model, 'geo_field': geo_field,
                              'id_field': id_field, 'fields': fields})
            }
        else:
            attrs = {
                '__module__': 'layerserver',
                'Meta': type('Meta', (object,), {'model': model,
                                                 'id_field': id_field,
                                                 'geo_field': geo_field})
            }
        serializer = type('%s_serializer' % str(model._meta.db_table),
                          (GeoFeatureModelSerializer,), attrs)

    else:

        if len(fields) > 0:
            attrs = {
                '__module__': 'layerserver',
                'Meta': type('Meta', (object,),
                             {'model': model, 'id_field': id_field,
                              'fields': fields})
            }
        else:
            attrs = {
                '__module__': 'layerserver',
                'Meta': type('Meta', (object,), {'model': model,
                                                 'id_field': id_field})
            }
        serializer = type('%s_serializer' % str(model._meta.db_table),
                          (serializers.ModelSerializer,), attrs)

    return serializer


class DBLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataBaseLayer
        fields = ['slug', 'name', 'pk_field', 'geom_field']


class DBLayerFieldListSerializer(serializers.ListSerializer):

    def to_representation(self, data):
        data = data.filter(enabled=True)
        return super(
            DBLayerFieldListSerializer, self).to_representation(data)


class DBLayerFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataBaseLayerField
        fields = ['field', 'alias']
        list_serializer_class = DBLayerFieldListSerializer


class DBLayerDetailSerializer(serializers.ModelSerializer):
    # TODO: serialize category
    fields = DBLayerFieldSerializer(many=True, read_only=True)

    def to_representation(self, obj):
        data = super(
            DBLayerDetailSerializer, self).to_representation(obj)
        data['style'] = {
                    'shapetype': obj.shapetype,
                    'shape_radius': obj.shape_radius,
                    'stroke_color': obj.stroke_color,
                    'stroke_width': obj.stroke_width,
                    'stroke_dash_array': obj.stroke_dash_array,
                    'fill_color': obj.fill_color,
                    'fill_opacity': obj.fill_opacity
            }

        return data

    class Meta:
        model = DataBaseLayer
        fields = ['slug', 'name', 'title', 'description', 'keywords',
                  'pk_field', 'geom_field', 'fields']
