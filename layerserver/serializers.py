# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict

from django.conf import settings
from django.contrib.gis.db import models

from rest_framework import serializers
from rest_framework_gis.serializers import (
    GeoFeatureModelSerializer, GeoFeatureModelListSerializer
)

from layerserver.models import (
    DataBaseLayer, DataBaseLayerField, DataBaseLayerReference
)


class Geom4326ListSerializer(GeoFeatureModelListSerializer):
    def update(self, instance, validated_data):
        id_field = self.child.__class__.Meta.id_field
        map_obj = {}
        for obj in instance:
            map_obj[getattr(obj, id_field)] = obj
        ret = []
        for i in range(len(validated_data)):
            data = validated_data[i]
            original = self.initial_data[i]
            if 'geometry' in original and type(original['geometry']) is dict:
                pk = original['id']
            else:
                pk = data[id_field]
            obj = map_obj[pk]
            ret.append(self.child.update(obj, data))
        return ret


class Geom4326Serializer(GeoFeatureModelSerializer):
    @classmethod
    def many_init(cls, *args, **kwargs):
        kwargs['child'] = cls()
        return Geom4326ListSerializer(*args, **kwargs)

    def to_representation(self, instance):
        """
        Serialize objects -> primitives.
        """
        # prepare OrderedDict geojson structure
        feature = OrderedDict()
        # the list of fields that will be processed by get_properties
        # we will remove fields that have been already processed
        # to increase performance on large numbers
        fields = list(self.fields.values())

        # optional id attribute
        if self.Meta.id_field:
            field = self.fields[self.Meta.id_field]
            value = field.get_attribute(instance)
            feature["id"] = field.to_representation(value)
            fields.remove(field)

        # required type attribute
        # must be "Feature" according to GeoJSON spec
        feature["type"] = "Feature"

        # required geometry attribute
        # MUST be present in output according to GeoJSON spec
        field = self.fields[self.Meta.geo_field]
        geo_value = field.get_attribute(instance)
        if geo_value and geo_value.srid != 4326:
            geo_value = geo_value.clone()
            geo_value.transform(4326)
        feature["geometry"] = field.to_representation(geo_value)
        fields.remove(field)
        # Bounding Box
        # if auto_bbox feature is enabled
        # bbox will be determined automatically automatically
        if self.Meta.auto_bbox and geo_value:
            feature["bbox"] = geo_value.extent
        # otherwise it can be determined via another field
        elif self.Meta.bbox_geo_field:
            field = self.fields[self.Meta.bbox_geo_field]
            value = field.get_attribute(instance)
            feature["bbox"] = value.extent if hasattr(
                value, 'extent') else None
            fields.remove(field)

        # GeoJSON properties
        feature["properties"] = self.get_properties(instance, fields)

        return feature

    def to_internal_value(self, data):
        internal_value = super(Geom4326Serializer, self).to_internal_value(data)
        if self.Meta.geo_field in internal_value and internal_value[self.Meta.geo_field] and \
                internal_value[self.Meta.geo_field].srid is None:
            internal_value[self.Meta.geo_field].srid = 4326
        return internal_value


SERIALIZER_FIELD_MAPPING = {
    models.AutoField: serializers.IntegerField,
    models.BigIntegerField: serializers.IntegerField,
    # models.BooleanField: serializers.BooleanField,
    models.CharField: serializers.CharField,
    models.CommaSeparatedIntegerField: serializers.CharField,
    models.DateField: serializers.DateField,
    models.DateTimeField: serializers.DateTimeField,
    models.DecimalField: serializers.DecimalField,
    models.EmailField: serializers.CharField,
    # models.Field: serializers.ModelField,
    # models.FileField: serializers.FileField,
    models.FloatField: serializers.FloatField,
    # models.ImageField: serializers.ImageField,
    models.IntegerField: serializers.IntegerField,
    # models.NullBooleanField: serializers.NullBooleanField,
    models.PositiveIntegerField: serializers.IntegerField,
    models.PositiveSmallIntegerField: serializers.IntegerField,
    models.SlugField: serializers.CharField,
    models.SmallIntegerField: serializers.IntegerField,
    models.TextField: serializers.CharField,
    models.TimeField: serializers.TimeField,
    models.URLField: serializers.CharField,
    models.GenericIPAddressField: serializers.CharField,
    models.FilePathField: serializers.CharField,
}


def create_dblayer_serializer(model, fields, id_field, map_id_field=False):
    if id_field is None or id_field == '':
        id_field = id

    geo_field = None
    for f in model._meta.fields:
        if isinstance(f, models.GeometryField):
            geo_field = str(f).split('.')[-1]
            break

    if geo_field is None:
        raise Exception('NO GEOM FIELD DEFINED')

    fields_serialize = fields[:]
    fields_serialize.remove(geo_field)

    if len(fields) > 0:
        attrs = {
            '__module__': 'layerserver',
            'Meta': type(str('Meta'), (object,),
                         {'model': model, 'geo_field': geo_field,
                          'id_field': id_field, 'fields': fields_serialize})
        }
    else:
        attrs = {
            '__module__': 'layerserver',
            'Meta': type(str('Meta'), (object,), {
                'model': model, 'id_field': id_field, 'geo_field': geo_field
            })
        }
    if map_id_field:
        for f in model._meta.fields:
            if f.column == id_field:
                fields = {}
                if f.__class__ in SERIALIZER_FIELD_MAPPING:
                    fields[id_field] = SERIALIZER_FIELD_MAPPING[f.__class__]()
                else:
                    raise Exception('id_field type NOT SUPPORTED')
                attrs.update(fields)
                break
    serializer = type(str('%s_serializer') % str(model._meta.db_table),
                      (Geom4326Serializer,), attrs)

    return serializer


class DBLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataBaseLayer
        fields = ['slug', 'name', 'pk_field', 'geom_field']


class DBLayerReferenceSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    def get_title(self, obj):
        if obj.service is None:
            return serializers.empty
        return obj.service.title or obj.service.name

    def get_url(self, obj):
        if obj.service is None:
            return serializers.empty
        url = ('%s/qgisserver/services/%s/' % (
            settings.GISCUBE_URL, obj.service.name)).replace('//', '')
        return url

    class Meta:
        model = DataBaseLayerReference
        fields = ['title', 'url']


class DBLayerFieldListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        data = data.filter(enabled=True)
        return super(
            DBLayerFieldListSerializer, self).to_representation(data)

class DBLayerFieldSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        data = super(
            DBLayerFieldSerializer, self).to_representation(obj)

        data['type'] = obj.type
        data['null'] = obj.null
        data['size'] = obj.size
        data['decimals'] = obj.decimals

        if obj.values_list_type == 'flatlist':
            rows = []
            for line in data['values_list'].splitlines():
                parts = line.split(',')
                if len(parts) == 1:
                    rows.append(parts[0])
                elif len(parts) == 2:
                    rows.append(parts)
                else:
                    rows.append('error')
            data['values_list'] = rows
        elif obj.values_list_type == 'sql':
            rows = []
            for r in obj.layer.db_connection.fetchall(obj.values_list):
                if len(r) == 1:
                    rows.append(r[0])
                else:
                    rows.append(r)
            data['values_list'] = rows
        else:
            del data['values_list']
        return data

    class Meta:
        model = DataBaseLayerField
        fields = ['name', 'label', 'search', 'fullsearch', 'values_list']
        list_serializer_class = DBLayerFieldListSerializer


class DBLayerDetailSerializer(serializers.ModelSerializer):
    # TODO: serialize category
    fields = DBLayerFieldSerializer(many=True, read_only=True)
    references = DBLayerReferenceSerializer(many=True, read_only=True)

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
                  'pk_field', 'geom_field', 'fields', 'references']
