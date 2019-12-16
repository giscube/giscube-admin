from collections import OrderedDict

from django.contrib.gis.db import models
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.urls import reverse

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from ..widgets import widgets_types


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


class UndoSerializerMixin(object):
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


class FixPropertiesSerializerMixin(object):
    def append_value(self, data, attribute, value):
        if isinstance(data.get('properties'), dict):
            data['properties'][attribute] = value
        else:
            data[attribute] = value


class ImageWithThumbnailFieldSerializer(serializers.FileField):
    pass


class ImageWithThumbnailSerializerMixin(object):
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
                value = self.fix_image_value(obj, attribute)
                self.append_value(data, attribute, value)
        return data


class VirtualFieldsSerializer(object):
    def to_representation(self, obj):
        data = super().to_representation(obj)
        for field in self.Meta.virtual_fields.values():
            value = field.widget_class.serialize_value(obj, field)
            if value:
                self.append_value(data, field.name, value)
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


class WidgetSerializerMixin(object):
    def create(self, validated_data):
        for field in self.__class__.Meta.model._meta.get_fields():
            if field._giscube_field['enabled']:
                widget_class = widgets_types[field._giscube_field['widget']]
                widget_class.create(self.context['request'], validated_data, field._giscube_field)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        for field in self.__class__.Meta.model._meta.get_fields():
            if field._giscube_field['enabled']:
                widget_class = widgets_types[field._giscube_field['widget']]
                widget_class.update(self.context['request'], instance, validated_data, field._giscube_field)
        return super().update(instance, validated_data)


class JSONSerializerFactory(object):
    common_mixins = (
        UndoSerializerMixin, WidgetSerializerMixin, AccessTokenMixin, FixPropertiesSerializerMixin,
        ImageWithThumbnailSerializerMixin, VirtualFieldsSerializer
    )
    serializer_class = JSONSerializer

    def __init__(self, model, fields, id_field, read_only_fields, virtual_fields=None):
        self.model = model
        self.fields = fields
        self.id_field = 'id' if id_field is None or id_field == '' else id_field
        self.read_only_fields = read_only_fields
        self.virtual_fields = virtual_fields or {}

    def to_image_field(self, field_name, field):
        field_kwargs = serializers.get_field_kwargs(field_name, field)
        kwargs = {}
        valid_attrs = ['max_length', 'required', 'allow_null']
        for k, v in field_kwargs.items():
            if k in valid_attrs:
                kwargs[k] = v
        return ImageWithThumbnailFieldSerializer(**kwargs)

    def apply_widgets(self, attrs, model, fields):
        from layerserver.model_legacy import ImageWithThumbnailField
        for field in fields:
            f = model._meta.get_field(field)
            if type(f) is ImageWithThumbnailField:
                attrs[field] = self.to_image_field(field, f)

    def get_attrs(self):
        attrs = {
            '__module__': 'layerserver',
            'Meta': type(str('Meta'), (object,), self.get_meta_attrs())
        }
        self.apply_widgets(attrs, self.model, self.fields)
        return attrs

    def get_fields_to_serialize(self):
        fields_to_serialize = self.fields[:]
        # pk field is always needed
        if self.id_field not in fields_to_serialize:
            fields_to_serialize.append(self.id_field)
        return fields_to_serialize

    def get_meta_attrs(self):
        extra_kwargs = {}
        for f in self.model._meta.fields:
            extra_kwargs[f.name] = {'required': not self.model._meta.get_field(f.name).blank}
        meta_attrs = {
            'model': self.model,
            'id_field': self.id_field,
            'map_id_field': self.id_field in self.fields,
            'extra_kwargs': extra_kwargs,
            'list_serializer_class': JSONModelListSerializer
        }

        if len(self.fields) > 0:
            meta_attrs['fields'] = self.get_fields_to_serialize()
        if len(self.read_only_fields) > 0:
            meta_attrs['read_only_fields'] = self.read_only_fields
        meta_attrs['virtual_fields'] = self.virtual_fields

        return meta_attrs

    def get_serializer(self):
        attrs = self.get_attrs()
        mixins = self.common_mixins + (self.serializer_class,)
        return type(str('%s_serializer') % str(self.model._meta.db_table), mixins, attrs)


class Geom4326SerializerFactory(JSONSerializerFactory):
    serializer_class = Geom4326Serializer

    def __init__(self, model, fields, id_field, read_only_fields, virtual_fields):
        super().__init__(model, fields, id_field, read_only_fields, virtual_fields)

        self.geo_field = None
        for f in model._meta.fields:
            if isinstance(f, models.GeometryField):
                self.geo_field = str(f).split('.')[-1]
                break

        if self.geo_field is None:
            raise Exception('NO GEOM FIELD DEFINED')

    def get_fields_to_serialize(self):
        fields = super().get_fields_to_serialize()
        if self.geo_field in fields:
            fields.remove(self.geo_field)
        return fields

    def get_meta_attrs(self):
        meta_attrs = super().get_meta_attrs()
        del meta_attrs['list_serializer_class']
        meta_attrs['geo_field'] = self.geo_field
        return meta_attrs


def create_dblayer_serializer(model, fields, id_field, read_only_fields, virtual_fields=None):
    if model._schema.get('geom_field', None):
        return Geom4326SerializerFactory(model, fields, id_field, read_only_fields, virtual_fields).get_serializer()
    else:
        return JSONSerializerFactory(model, fields, id_field, read_only_fields, virtual_fields).get_serializer()
