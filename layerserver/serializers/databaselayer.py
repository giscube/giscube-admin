import json

from django.conf import settings
from django.urls import reverse

from rest_framework import serializers

from layerserver.model_legacy import create_dblayer_model
from layerserver.models import DataBaseLayer, DataBaseLayerReference
from giscube.utils import remove_app_url, url_slash_join

from .dblayer_field import DBLayerFieldSerializer
from .dblayer_virtualfield import DBLayerVirtualFieldSerializer


class DBLayerSerializer(serializers.ModelSerializer):
    def to_representation(self, obj):
        data = super().to_representation(obj)
        data['title'] = obj.title or obj.name
        return data

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
        return url_slash_join(settings.GISCUBE_URL, '/qgisserver/services/%s/' % obj.service.name)

    def to_representation(self, obj):
        data = super().to_representation(obj)
        data['type'] = 'WMS'
        data['auth'] = None
        data['options'] = {}

    class Meta:
        model = DataBaseLayerReference
        fields = ['title', 'url', 'refresh']


def style_representation(obj):
    res = {'shapetype': obj.shapetype}
    fields = {
        'marker': ['marker_color', 'icon_type', 'icon', 'icon_color'],
        'line': ['stroke_color', 'stroke_width', 'stroke_opacity', 'stroke_dash_array'],
        'polygon': ['stroke_color', 'stroke_width', 'stroke_opacity', 'stroke_dash_array', 'fill_color',
                    'fill_opacity'],
        'circle': ['shape_radius', 'stroke_color', 'stroke_width', 'stroke_opacity', 'stroke_dash_array',
                   'fill_color',
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
        'line': ['stroke_color', 'stroke_width', 'stroke_opacity', 'stroke_dash_array'],
        'polygon': ['stroke_color', 'stroke_width', 'stroke_opacity', 'stroke_dash_array', 'fill_color',
                    'fill_opacity'],
        'circle': ['shape_radius', 'stroke_color', 'stroke_width', 'stroke_opacity', 'stroke_dash_array', 'fill_color',
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
    title = serializers.SerializerMethodField()
    # TODO: serialize category
    fields = DBLayerFieldSerializer(many=True, read_only=True)
    virtual_fields = DBLayerVirtualFieldSerializer(many=True, read_only=True)
    references = DBLayerReferenceSerializer(many=True, read_only=True)

    def get_title(self, obj):
        return obj.title or obj.name

    def format_options_json(self, obj, data):
        return data.update({
            'objects_path': 'data',
            'attributes_path': None
        })

    def format_options_geojson(self, obj, data):
        return data.update({
            'objects_path': 'features',
            'attributes_path': 'properties',
            'geom_path': 'geometry'
        })

    def to_representation(self, obj):
        data = super().to_representation(obj)
        data['pagination'] = {
            'page_size': obj.get_page_size(),
            'max_page_size': obj.get_max_page_size()
        }
        data['design'] = {
            'list_fields': obj.list_fields,
            'form_fields': obj.form_fields
        }
        if obj.geom_field is None:
            data['geom_type'] = None
            self.format_options_json(obj, data)
        else:
            Layer = create_dblayer_model(obj)
            field = Layer._meta.get_field(obj.geom_field)
            data['geom_type'] = field.geom_type
            data['design']['popup'] = obj.popup
            self.format_options_geojson(obj, data)
            data['style'] = style_representation(obj)
            data['style_rules'] = style_rules_representation(obj)
            data['design']['tooltip'] = obj.tooltip
            data['design']['cluster'] = json.loads(obj.cluster_options or '{}') if obj.cluster_enabled else None

            if obj.wms_as_reference:
                path = reverse('content-wms', kwargs={'name': obj.name})
                request = self.context['request'] if 'request' in self.context else None
                if request:
                    url = request.build_absolute_uri(path)
                else:
                    url = url_slash_join(settings.GISCUBE_URL, remove_app_url(path))
                reference = {
                    'title': data['title'],
                    'url': url,
                    'type': 'WMS',
                    'auth': 'token' if not obj.anonymous_view else None,
                    'options': {
                        'layers': data['name'],
                        'format': 'image/png',
                        'transparent': True,
                        'uppercase': True
                    }
                }
                data['references'].insert(0, reference)

        return data

    class Meta:
        model = DataBaseLayer
        fields = ['name', 'title', 'description', 'keywords', 'pk_field', 'geom_field', 'fields', 'virtual_fields',
                  'references']
