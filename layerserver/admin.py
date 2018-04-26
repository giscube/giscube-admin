# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import ujson as json
import requests


from django.conf import settings
from django.contrib import admin
from django.core.files.base import ContentFile
from django.utils.translation import gettext as _
from django.utils import timezone

from django_vue_tabs.admin import TabsMixin

from .models import GeoJsonLayer
from giscube.utils import unique_service_directory


@admin.register(GeoJsonLayer)
class GeoJsonLayerAdmin(TabsMixin, admin.ModelAdmin):
    list_display = ('name', 'title',)
    search_fields = ('name', 'title', 'keywords')

    tabs = (
        (_('Information'), ('fieldset-information',)),
        (_('Data'), ('fieldset-data',)),
        (_('Style'), ('fieldset-style',))
    )

    fieldsets = [
        (None, {
            'fields': [
                'category', 'name', 'title',
                'description', 'keywords', 'active', 'visibility',
                'visible_on_geoportal',
            ],
            'classes': ('fieldset-information',),
        }),
        (None, {
            'fields': [
                'url', 'data_file', 'cache_time', 'last_fetch_on',
                'generated_on',
            ],
            'classes': ('fieldset-data',),
        }),
        (None, {
            'fields': [
                'shapetype', 'shape_radius', 'stroke_color', 'stroke_width',
                'stroke_dash_array', 'fill_color', 'fill_opacity',
            ],
            'classes': ('fieldset-style',),
        }),
    ]

    def generateGeoJsonLayer(self, layer):
        path = os.path.join(settings.MEDIA_ROOT, layer.data_file.path)
        data = json.load(open(path))
        data['metadata'] = layer.metadata
        fixed_file = os.path.join(
            settings.MEDIA_ROOT, layer.service_path, 'data.json')
        with open(path, "wb") as fixed_file:
            fixed_file.write(json.dumps(data))

    # TODO: validate both data_file and url
    def save_model(self, request, obj, form, change):
        super(GeoJsonLayerAdmin, self).save(request, obj, form, change)
        if obj.url:
            if not obj.service_path:
                unique_service_directory(obj)
                try:
                    r = requests.get(obj.url)
                    content = ContentFile(r.text)
                    obj.data_file.save('remote.json', content, save=True)
                    obj.last_fetch_on = timezone.localtime()
                except Exception:
                    pass
                obj.save()
                self.generateGeoJsonLayer(obj)
        else:
            if 'data_file' in form.changed_data:
                self.generateGeoJsonLayer(obj)

        # Cas fitxer
        # - si ha canviat cal generar el corregit
        # Cas url
        # - descarregar i guardar i corregir
