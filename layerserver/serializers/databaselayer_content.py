from collections import OrderedDict

from django.contrib.gis.db import models
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.urls import reverse

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer


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


class JSONModelListSerializer(serializers.ListSerializer):
    @property
    def data(self):
        return super(serializers.ListSerializer, self).data

    def to_representation(self, data):
        return OrderedDict((
            ('data', super().to_representation(data)),
        ))


class JSONSerializer(serializers.ModelSerializer):
    @classmethod
    def many_init(cls, *args, **kwargs):
        kwargs['child'] = cls()
        return JSONModelListSerializer(*args, **kwargs)


class UndoSerializerMixin(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        self.instance = None
        return super().__init__(*args, **kwargs)

    def create(self, validated_data):
        """
        Init instance, needed to undo
        """
        ModelClass = self.Meta.model
        instance = ModelClass()
        self.instance = instance
        for key, value in validated_data.items():
            setattr(instance, key, value)
        return super().create(validated_data)

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
        return super().save(**kwargs)


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
            pk = getattr(obj, obj._schema['pk_field'])
            kwargs = {'name': obj._schema['name'], 'pk': pk, 'attribute': attribute, 'path': value.name}
            url = reverse('content-detail-file-value', kwargs=kwargs)
            url = self.append_token(self.context['request'].build_absolute_uri(url))
            res = {
                'src': url
            }
            thumbnail = value.storage.get_thumbnail(value.name)
            if thumbnail:
                kwargs = {'name': obj._schema['name'], 'pk': pk, 'attribute': attribute,
                          'path': thumbnail['name']}
                url = reverse('content-detail-thumbnail-value', kwargs=kwargs)
                url = self.context['request'].build_absolute_uri(url)
                res['thumbnail'] = self.append_token(url)
            return res

    def to_representation(self, obj):
        data = super().to_representation(obj)
        for attribute, field in list(self.fields.items()):
            if isinstance(field, ImageWithThumbnailFieldSerializer):
                if 'properties' in data and isinstance(data['properties'], dict):
                    data['properties'][attribute] = self.fix_image_value(obj, attribute)
                else:
                    data[attribute] = self.fix_image_value(obj, attribute)
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

    fields_to_serialize = fields[:]

    # pk field is always needed
    if id_field not in fields_to_serialize:
        fields_to_serialize.append(id_field)

    meta_attrs = {
        'model': model, 'id_field': id_field,
        'map_id_field': map_id_field,
        'extra_kwargs': extra_kwargs,
        'list_serializer_class': JSONModelListSerializer
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
        UndoSerializerMixin, AccessTokenMixin, ImageWithThumbnailSerializer, JSONSerializer,), attrs)

    return serializer


def create_dblayer_geom_serializer(model, fields, id_field, read_only_fields):
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
    if geo_field in fields_to_serialize:
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
