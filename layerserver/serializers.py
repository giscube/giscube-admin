from django.conf import settings
from django.contrib.gis.db import models
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.urls import reverse

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from layerserver.model_legacy import create_dblayer_model
from layerserver.models import DataBaseLayer, DataBaseLayerReference, GeoJsonLayer

from .serializers_dblayer_field import DBLayerFieldSerializer


class GeoJSONLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoJsonLayer
        fields = ['name', 'title']


class Geom4326Serializer(GeoFeatureModelSerializer):
    def to_representation(self, instance):
        data = super(Geom4326Serializer, self).to_representation(instance)
        field = self.fields[self.Meta.geo_field]
        geo_value = field.get_attribute(instance)
        if geo_value and geo_value.srid != 4326:
            geo_value = geo_value.clone()
            geo_value.transform(4326)
            data["geometry"] = field.to_representation(geo_value)
        # Remove id_field if it exists in properties
        if not self.Meta.map_id_field and self.Meta.id_field in data['properties']:
            del data['properties'][self.Meta.id_field]
        # Add id_field if it not exists in properties
        if self.Meta.map_id_field and self.Meta.id_field not in data['properties']:
            field = self.fields[self.Meta.id_field]
            data['properties'][self.Meta.id_field] = field.get_attribute(instance)
        return data

    def to_internal_value(self, data):
        internal_value = super(Geom4326Serializer, self).to_internal_value(data)
        if self.Meta.geo_field in internal_value and internal_value[self.Meta.geo_field] and \
                internal_value[self.Meta.geo_field].srid is None:
            internal_value[self.Meta.geo_field].srid = 4326
        return internal_value


class UndoSerializerMixin(object):
    def __init__(self, *args, **kwargs):
        self.instance = None
        return super(Geom4326Serializer, self).__init__(*args, **kwargs)

    def create(self, validated_data):
        """
        Init instance, needed to undo
        """
        ModelClass = self.Meta.model
        instance = ModelClass()
        self.instance = instance
        for key, value in validated_data.items():
            setattr(instance, key, value)
        return super(Geom4326Serializer, self).create(validated_data)

    def save(self, **kwargs):
        """
        Clean files
        """
        if self.instance is not None:
            for k, v in self.fields.items():
                if isinstance(v, serializers.FileField) and k in self.validated_data:
                    old_value = getattr(self.instance, k)
                    new_value = self.validated_data[k]
                    if old_value is not None and (
                            new_value is None or isinstance(new_value, UploadedFile)):
                        transaction.on_commit(
                            lambda: old_value.delete(save=False)
                        )
        return super(UndoSerializerMixin, self).save(**kwargs)


class AccessTokenMixin(object):
    def append_token(self, url):
        token = None
        auth = getattr(self.context['request'], 'auth', None)
        if hasattr(auth, 'token'):
            token = self.context['request'].auth.token
        if token:
            url = '%s?access_token=%s' % (url, token)
        return url


class ImageWithThumbnailFieldSerializer(serializers.FileField):
    pass


class ImageWithThumbnailSerializer(object):
    def fix_image_value(self, obj, attribute):
        image_options = getattr(obj, attribute).field.widget_options
        value = getattr(obj, attribute)
        if value is None or value.name is None or value.name.strip() == '':
            return None

        if 'base_url' in image_options and image_options['base_url'] is not None:
            if value:
                res = {
                    'src': value.storage.url(value.name)
                }
                thumbnail = value.storage.get_thumbnail(value.name)
                if thumbnail:
                    res['thumbnail'] = thumbnail['url']
                return res
        else:
            layer = obj.get_layer()
            pk = getattr(obj, layer.pk_field)
            kwargs = {'name': layer.name, 'pk': pk, 'attribute': attribute, 'path': value.name}
            url = reverse('content-detail-file-value', kwargs=kwargs)
            url = self.append_token(self.context['request'].build_absolute_uri(url))
            res = {
                'src': url
            }
            thumbnail = value.storage.get_thumbnail(value.name)
            if thumbnail:
                kwargs = {'name': layer.name, 'pk': pk, 'attribute': attribute,
                          'path': thumbnail['path']}
                url = reverse('content-detail-thumbnail-value', kwargs=kwargs)
                url = self.context['request'].build_absolute_uri(url)
                res['thumbnail'] = self.append_token(url)
            return res

    def to_representation(self, obj):
        data = super().to_representation(obj)
        for attribute, field in list(self.fields.items()):
            if isinstance(field, ImageWithThumbnailFieldSerializer):
                data['properties'][attribute] = self.fix_image_value(obj, attribute)
        return data


SERIALIZER_ID_FIELD_MAPPING = {
    models.AutoField: serializers.IntegerField,
    models.BigIntegerField: serializers.IntegerField,
    models.CharField: serializers.CharField,
    models.DateField: serializers.DateField,
    models.DateTimeField: serializers.DateTimeField,
    models.DecimalField: serializers.DecimalField,
    models.EmailField: serializers.CharField,
    models.FloatField: serializers.FloatField,
    models.IntegerField: serializers.IntegerField,
    models.PositiveIntegerField: serializers.IntegerField,
    models.PositiveSmallIntegerField: serializers.IntegerField,
    models.SmallIntegerField: serializers.IntegerField,
    models.TextField: serializers.CharField,
    models.TimeField: serializers.TimeField,
}


def to_image_field(field_name, field):
    field_kwargs = serializers.get_field_kwargs(field_name, field)
    kwargs = {}
    valid_attrs = ['max_length', 'required', 'allow_null']
    for k, v in field_kwargs.items():
        if k in valid_attrs:
            kwargs[k] = v
    return ImageWithThumbnailFieldSerializer(**kwargs)


def apply_widgets(attrs, model, fields):
    from layerserver.model_legacy import ImageWithThumbnailField
    for field in fields:
        f = model._meta.get_field(field)
        if type(f) is ImageWithThumbnailField:
            attrs[field] = to_image_field(field, f)


def create_dblayer_serializer(model, fields, id_field, read_only_fields):
    if id_field is None or id_field == '':
        id_field = id

    map_id_field = id_field in fields

    extra_kwargs = {}
    for f in model._meta.fields:
        extra_kwargs[f.name] = {'required': not model._meta.get_field(f.name).blank}

    geo_field = None
    for f in model._meta.fields:
        if isinstance(f, models.GeometryField):
            geo_field = str(f).split('.')[-1]
            break

    if geo_field is None:
        raise Exception('NO GEOM FIELD DEFINED')

    fields_to_serialize = fields[:]
    fields_to_serialize.remove(geo_field)

    # pk field is always needed by Geom4326Serializer
    if id_field not in fields_to_serialize:
        fields_to_serialize.append(id_field)

    meta_attrs = {
        'model': model, 'geo_field': geo_field, 'id_field': id_field,
        'map_id_field': map_id_field,
        'extra_kwargs': extra_kwargs
    }
    attrs = {
        '__module__': 'layerserver',
        'Meta': type(str('Meta'), (object,), meta_attrs)
    }

    if len(fields) > 0:
        setattr(attrs['Meta'], 'fields', fields_to_serialize)
    if len(read_only_fields) > 0:
        setattr(attrs['Meta'], 'read_only_fields', read_only_fields)

    apply_widgets(attrs, model, fields)
    serializer = type(str('%s_serializer') % str(model._meta.db_table), (
        UndoSerializerMixin, AccessTokenMixin, ImageWithThumbnailSerializer, Geom4326Serializer,), attrs)

    return serializer


class DBLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataBaseLayer
        fields = ['name', 'pk_field', 'geom_field']


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


def style_representation(obj):
    res = {'shapetype': obj.shapetype}
    fields = {
        'marker': ['marker_color', 'icon_type', 'icon', 'icon_color'],
        'line': ['stroke_color', 'stroke_width', 'stroke_dash_array'],
        'polygon': ['stroke_color', 'stroke_width', 'stroke_dash_array', 'fill_color', 'fill_opacity'],
        'circle': ['shape_radius', 'stroke_color', 'stroke_width', 'stroke_dash_array', 'fill_color',
                   'fill_opacity'],
        'image': ['icon'],
    }
    if obj.shapetype in fields:
        for attr in fields[obj.shapetype]:
            res[attr] = getattr(obj, attr)
    return res


def style_rules_representation(obj):
    style_rules = []
    fields = {
        'marker': ['marker_color', 'icon_type', 'icon', 'icon_color'],
        'line': ['stroke_color', 'stroke_width', 'stroke_dash_array'],
        'polygon': ['stroke_color', 'stroke_width', 'stroke_dash_array', 'fill_color', 'fill_opacity'],
        'circle': ['shape_radius', 'stroke_color', 'stroke_width', 'stroke_dash_array', 'fill_color',
                   'fill_opacity'],
    }
    for rule in obj.rules.all():
        style_rule = {
            'field': rule.field,
            'comparator': rule.comparator,
            'value': rule.value,
        }
        if obj.shapetype in fields:
            for attr in fields[obj.shapetype]:
                style_rule[attr] = getattr(rule, attr)
        style_rules.append(style_rule)
    return style_rules


class DBLayerDetailSerializer(serializers.ModelSerializer):
    # TODO: serialize category
    fields = DBLayerFieldSerializer(many=True, read_only=True)
    references = DBLayerReferenceSerializer(many=True, read_only=True)

    def to_representation(self, obj):
        data = super(
            DBLayerDetailSerializer, self).to_representation(obj)
        data['style'] = style_representation(obj)
        data['style_rules'] = style_rules_representation(obj)
        data['design'] = {
            'list_fields': obj.list_fields,
            'form_fields': obj.form_fields,
            'popup': obj.popup
        }
        data['pagination'] = {
            'page_size': obj.get_page_size(),
            'max_page_size': obj.get_max_page_size()
        }
        Layer = create_dblayer_model(obj)
        data['geom_type'] = None
        if obj.geom_field is not None:
            field = Layer._meta.get_field(obj.geom_field)
            data['geom_type'] = field.geom_type

        return data

    class Meta:
        model = DataBaseLayer
        fields = ['name', 'title', 'description', 'keywords',
                  'pk_field', 'geom_field', 'fields', 'references']
