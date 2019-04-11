# -*- coding: utf-8 -*-
from django.db import transaction
from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _

from django_vue_tabs.admin import TabsMixin

from giscube.utils import unique_service_directory
from layerserver.admin_forms import (
    DataBaseLayerAddForm, DataBaseLayerChangeForm
)
from layerserver.models import (
    GeoJsonLayer, DataBaseLayer, DataBaseLayerField,
    DBLayerGroup, DBLayerUser, DataBaseLayerReference
)
from layerserver.tasks import async_geojsonlayer_refresh


@admin.register(GeoJsonLayer)
class GeoJsonLayerAdmin(TabsMixin, admin.ModelAdmin):
    change_form_template = 'admin/layerserver/geojson_layer/change_form.html'
    autocomplete_fields = ('category',)
    list_display = ('name', 'title', 'url_data')
    search_fields = ('name', 'title', 'keywords')
    readonly_fields = ('last_fetch_on', 'generated_on', 'url_data')
    save_as = True

    tabs = (
        (_('Information'), ('fieldset-information',)),
        (_('GEOJson'), ('fieldset-geojson',)),
        (_('Permissions'), ('tab-permissions',)),
        (_('Style'), ('fieldset-style',)),
        (_('Design'), ('tab-design',)),
    )

    fieldsets = [
        (None, {
            'fields': [
                'category', 'name', 'title',
                'description', 'keywords', 'active', 'visibility', 'visible_on_geoportal',
            ],
            'classes': ('fieldset-information',),
        }),
        (None, {
            'fields': [
                'url', 'headers', 'data_file', 'cache_time', 'last_fetch_on',
                'generated_on',
            ],
            'classes': ('fieldset-geojson',),
        }),
        (None, {
            'fields': [
                'shapetype', 'marker_color', 'icon_type', 'icon', 'icon_color', 'shape_radius', 'stroke_color',
                'stroke_width', 'stroke_dash_array', 'fill_color', 'fill_opacity',
            ],
            'classes': ('fieldset-style',),
        }),
        (None, {
            'fields': ['popup'],
            'classes': ('tab-design',),
        }),
    ]

    def url_data(self, obj):
        url = reverse('admin-api-geojsonlayer-detail', kwargs={'name': obj.name})
        return format_html('<a href="{url}" target="_blank">URL</a>', url=url)
    url_data.short_description = 'URL'

    def save_model(self, request, obj, form, change):
        if not obj.service_path:
            unique_service_directory(obj)
        super(GeoJsonLayerAdmin, self).save_model(request, obj, form, change)
        if obj.url:
            messages.info(request, '[%s] will be requested in background.' % obj.url)
        elif obj.data_file:
            messages.info(request, 'GeoJsonLayer will be generated/updated in background.')
        transaction.on_commit(
            lambda: async_geojsonlayer_refresh.delay(obj.pk)
        )


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
    ordering = ('name',)

    can_delete = False
    fields = ('enabled', 'readonly', 'name', 'label', 'get_type', 'get_size', 'get_decimals', 'get_null', 'search',
              'fullsearch', 'widget', 'widget_options',)
    readonly_fields = ('name', 'get_type', 'get_size', 'get_decimals', 'get_null')
    classes = ('tab-fields',)

    def has_add_permission(self, request):
        return False

    def get_type(self, obj):
        return obj.field_type or ''
    get_type.short_description = "Type"

    def get_size(self, obj):
        return obj.size or ''
    get_size.short_description = "Size"

    def get_decimals(self, obj):
        return obj.decimals or ''
    get_decimals.short_description = "Decimals"

    def get_null(self, obj):
        if obj.null is None:
            return ''
        else:
            return obj.null
    get_null.short_description = "Null"


class DataBaseLayerReferencesInline(admin.TabularInline):
    model = DataBaseLayerReference
    extra = 0

    fields = ('service',)
    classes = ('tab-references',)


@admin.register(DataBaseLayer)
class DataBaseLayerAdmin(TabsMixin, admin.ModelAdmin):
    add_form_template = 'admin/layerserver/database_layer/add_form.html'
    change_form_template = 'admin/layerserver/database_layer/change_form.html'

    autocomplete_fields = ['category']
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('slug', 'name', 'table', 'db_connection', 'api_metadata', 'api_data')
    list_display_links = ('slug', 'name', 'table')
    list_filter = ('db_connection',)
    inlines = []

    add_fieldsets = (
        ('Layer', {
            'fields': ('db_connection', 'geometry_columns', 'slug', 'name', 'table', 'geom_field', 'srid', 'pk_field')
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
        (_('Design'), ('tab-design',)),
    )

    edit_fieldsets = [
        (None, {
            'fields': [
                'category', 'slug', 'name', 'title',
                'description', 'keywords', 'active',
                'visible_on_geoportal',
                ('allow_page_size_0', 'page_size', 'max_page_size',),
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
                'shapetype', 'marker_color', 'icon_type', 'icon', 'icon_color', 'shape_radius', 'stroke_color',
                'stroke_width', 'stroke_dash_array', 'fill_color', 'fill_opacity',
            ],
            'classes': ('tab-style',),
        }),
        ('Anonymous user', {
            'fields': [
                ('anonymous_view', 'anonymous_add', 'anonymous_update', 'anonymous_delete',)
            ],
            'classes': ('tab-permissions',),
        }),
        (None, {
            'fields': [
                'list_fields', 'form_fields', 'popup'
            ],
            'classes': ('tab-design',),
        }),
    ]

    def api_data(self, obj):
        url = reverse('admin-api-layer-content-list', kwargs={'layer_slug': obj.slug})
        return format_html('<a href="{url}" target="_blank">API DATA</a>', url=url)
    api_data.short_description = 'API DATA'

    def api_metadata(self, obj):
        url = reverse('admin-api-layer-detail', kwargs={'slug': obj.slug})
        return format_html('<a href="{url}" target="_blank">API METADATA</a>', url=url)
    api_data.short_description = 'API METADATA'

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('table', 'geom_field', 'srid', 'api_metadata', 'api_data')
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
        conn = self.model.objects.get(pk=object_id)
        conn_status = self.model.objects.get(pk=object_id).db_connection.check_connection()
        if not conn_status:
            msg = 'ERROR: There was an error when connecting to: %s' % conn.db_connection
            messages.add_message(request, messages.ERROR, msg)

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
            defaults['form'] = DataBaseLayerAddForm
        else:
            defaults['form'] = DataBaseLayerChangeForm
        defaults.update(kwargs)
        return super(
            DataBaseLayerAdmin, self).get_form(request, obj, **defaults)

    def response_add(self, request, obj, post_url_continue=None):
        pass
        from django.contrib.admin.options import IS_POPUP_VAR

        if '_addanother' not in request.POST and IS_POPUP_VAR not in request.POST:
            request.POST = request.POST.copy()
            request.POST['_continue'] = 1
        return super().response_add(request, obj, post_url_continue)
