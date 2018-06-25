# -*- coding: utf-8 -*-

import os
import ujson as json
import requests


from django.conf import settings
from django.contrib import admin
from django.core.files.base import ContentFile
from django.utils.translation import gettext as _
from django.utils import timezone

from django_vue_tabs.admin import TabsMixin

from layerserver.admin_forms import (
    DataBaseLayerAddForm, DataBaseLayerChangeForm
)
from layerserver.models import (
    GeoJsonLayer, DataBaseLayer, DataBaseLayerField,
    DBLayerGroup, DBLayerUser, DataBaseLayerReference
)

from giscube.utils import unique_service_directory


@admin.register(GeoJsonLayer)
class GeoJsonLayerAdmin(TabsMixin, admin.ModelAdmin):
    list_display = ('name', 'title',)
    search_fields = ('name', 'title', 'keywords')

    tabs = (
        (_('Information'), ('fieldset-information',)),
        (_('GEOJson'), ('fieldset-geojson',)),
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
            'classes': ('fieldset-geojson',),
        }),
        (None, {
            'fields': [
                'shapetype', 'shape_radius', 'stroke_color', 'stroke_width',
                'stroke_dash_array', 'fill_color', 'fill_opacity',
            ],
            'classes': ('fieldset-style',),
        }),
    ]


    # TODO: validate both data_file and url
    def save_model(self, request, obj, form, change):
        if not obj.service_path:
            unique_service_directory(obj)
        if obj.url:
            try:
                r = requests.get(obj.url)
            except Exception as e:
                print('Error getting file %s' % e)
            else:
                content = ContentFile(r.text)
                if content:
                    remote_file = os.path.join(
                        settings.MEDIA_ROOT, obj.service_path, 'remote.json')
                    if os.path.exists(remote_file):
                        os.remove(remote_file)
                    obj.data_file.save('remote.json', content, save=True)
                    obj.last_fetch_on = timezone.localtime()

        super(GeoJsonLayerAdmin, self).save_model(request, obj, form, change)


class DBLayerGroupInline(admin.TabularInline):
    model = DBLayerGroup
    extra = 1
    classes = ('tab-permissions',)
    verbose_name = _('Group')
    verbose_name_plural = _('Groups')


class DBLayerUserInline(admin.TabularInline):
    model = DBLayerUser
    extra = 1
    classes = ('tab-permissions',)
    verbose_name = _('User')
    verbose_name_plural = _('Users')


class DataBaseLayerFieldsInline(admin.TabularInline):
    model = DataBaseLayerField
    extra = 0

    can_delete = False
    fields = ('enabled', 'field', 'alias', 'search', 'fullsearch')
    readonly_fields = ('field',)
    classes = ('tab-fields',)

    def has_add_permission(self, request):
        return False


class DataBaseLayerReferencesInline(admin.TabularInline):
    model = DataBaseLayerReference
    extra = 0

    fields = ('service',)
    classes = ('tab-references',)


@admin.register(DataBaseLayer)
class DataBaseLayerAdmin(TabsMixin, admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('slug', 'name', 'table')
    list_display_links = list_display
    inlines = []

    add_fieldsets = (
        ('Layer', {
            'fields': ('db_connection', 'slug', 'name', 'table', 'geom_field',
                       'srid')
        }),
    )
    tabs = None
    edit_tabs = (
        (_('Information'), ('tab-information',)),
        (_('Data base'), ('tab-data-base',)),
        (_('Fields'), ('tab-fields',)),
        (_('Style'), ('tab-style',)),
        (_('Permissions'), ('tab-permissions',)),
        (_('References'), ('tab-references',)),

    )

    edit_fieldsets = [
        (None, {
            'fields': [
                'category', 'slug', 'name', 'title',
                'description', 'keywords', 'active', 'visibility',
                'visible_on_geoportal',
            ],
            'classes': ('tab-information',),
        }),
        (None, {
            'fields': [
                'db_connection', 'table', 'pk_field', 'geom_field', 'srid'
            ],
            'classes': ('tab-data-base',),
        }),
        (None, {
            'fields': [
                'shapetype', 'shape_radius', 'stroke_color', 'stroke_width',
                'stroke_dash_array', 'fill_color', 'fill_opacity',
            ],
            'classes': ('tab-style',),
        }),
        ('Anonymous user', {
            'fields': [
                'anonymous_view', 'anonymous_add', 'anonymous_update',
                'anonymous_delete'
            ],
            'classes': ('tab-permissions',),
        }),
    ]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('table', 'geom_field', 'srid')
        return self.readonly_fields

    def add_view(self, request, form_url='', extra_context=None):
        self.fieldsets = self.add_fieldsets
        self.inlines = []
        return super(DataBaseLayerAdmin, self).add_view(
            request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.tabs = self.edit_tabs
        self.fieldsets = self.edit_fieldsets

        self.inlines = [DataBaseLayerFieldsInline, DBLayerUserInline,
                        DBLayerGroupInline, DataBaseLayerReferencesInline]
        return super(DataBaseLayerAdmin,
                     self).change_view(
                         request, object_id, form_url,
                         extra_context=extra_context)

    def get_form(self, request, obj=None, **kwargs):
        """
        Override add_form template
        """
        defaults = {}
        if obj is None:
            self.add_form_template = 'admin/data_base_layer/add_form.html'
            defaults['form'] = DataBaseLayerAddForm
        else:
            defaults['form'] = DataBaseLayerChangeForm
        defaults.update(kwargs)
        return super(
            DataBaseLayerAdmin, self).get_form(request, obj, **defaults)
