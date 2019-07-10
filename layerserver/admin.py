from django.contrib import admin, messages
from django.db import transaction
from django.urls import reverse
from django.utils.html import format_html, mark_safe
from django.utils.translation import gettext as _

from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from django_vue_tabs.admin import TabsMixin

from giscube.utils import unique_service_directory

from .admin_actions import geojsonlayer_force_refresh_data
from .admin_filters import DataBaseLayerGeomNullFilter
from .admin_forms import (DataBaseLayerAddForm, DataBaseLayerChangeForm, DataBaseLayerFieldsInlineForm,
                          DataBaseLayerStyleRuleInlineForm, DataBaseLayerVirtualFieldsInlineForm, GeoJsonLayerAddForm,
                          GeoJsonLayerChangeForm, GeoJsonLayerStyleRuleInlineForm)
from .models import (DataBaseLayer, DataBaseLayerField, DataBaseLayerReference, DataBaseLayerStyleRule,
                     DataBaseLayerVirtualField, DBLayerGroup, DBLayerUser, GeoJsonLayer, GeoJsonLayerStyleRule)
from .tasks import async_geojsonlayer_refresh
from .widgets import widgets_types


class StyleRuleInlineMixin(admin.StackedInline):
    model = GeoJsonLayerStyleRule
    extra = 0
    classes = ('tab-style',)
    fields = ('order', ('field', 'comparator', 'value'), 'marker_color', ('icon_type', 'icon', 'icon_color'),
              'shape_radius', ('stroke_color', 'stroke_width', 'stroke_opacity', 'stroke_dash_array'),
              ('fill_color', 'fill_opacity'))
    verbose_name = _('Rule')
    verbose_name_plural = _('Rules')


class GeoJsonLayerStyleRuleInline(StyleRuleInlineMixin):
    model = GeoJsonLayerStyleRule
    form = GeoJsonLayerStyleRuleInlineForm


@admin.register(GeoJsonLayer)
class GeoJsonLayerAdmin(TabsMixin, admin.ModelAdmin):
    change_form_template = 'admin/layerserver/geojson_layer/change_form.html'
    autocomplete_fields = ('category',)
    list_display = ('name', 'title', 'view_layer', 'public_url')
    list_filter = (('category', RelatedDropdownFilter), 'visibility', 'visible_on_geoportal', 'shapetype')
    search_fields = ('name', 'title', 'keywords')
    readonly_fields = ('last_fetch_on', 'generated_on', 'view_layer', 'public_url')
    inlines = [GeoJsonLayerStyleRuleInline]
    actions = [geojsonlayer_force_refresh_data]
    save_as = True

    tabs = (
        (_('Information'), ('tab-information',)),
        (_('GeoJSON'), ('tab-geojson',)),
        (_('Style'), ('tab-style',)),
        (_('Design'), ('tab-design',)),
    )

    add_fieldsets = [
        (None, {
            'fields': [
                'category', 'name', 'title',
                'description', 'keywords', 'active', 'visibility', 'visible_on_geoportal',
            ],
            'classes': ('tab-information',),
        }),
        (None, {
            'fields': [
                'url', 'headers', 'data_file', ('cache_time', 'max_outdated_time',), 'last_fetch_on',
                'generated_on',
            ],
            'classes': ('tab-geojson',),
        }),
        (None, {
            'fields': [
                'shapetype', 'marker_color', 'icon_type', 'icon', 'icon_color', 'shape_radius', 'stroke_color',
                'stroke_width', 'stroke_opacity', 'stroke_dash_array', 'fill_color', 'fill_opacity',
            ],
            'classes': ('tab-style',),
        }),
        (None, {
            'fields': ['popup'],
            'classes': ('tab-design',),
        }),
    ]

    edit_fieldsets = [
        (None, {
            'fields': [
                'category', 'name', 'title',
                'description', 'keywords', 'active', 'visibility', 'visible_on_geoportal',
            ],
            'classes': ('tab-information',),
        }),
        (None, {
            'fields': [
                'url', 'headers', 'data_file', ('cache_time', 'max_outdated_time',), 'last_fetch_on',
                'generated_on', 'force_refresh_data_file',
            ],
            'classes': ('tab-geojson',),
        }),
        (None, {
            'fields': [
                'shapetype', 'marker_color', 'icon_type', 'icon', 'icon_color', 'shape_radius', 'stroke_color',
                'stroke_width', 'stroke_opacity', 'stroke_dash_array', 'fill_color', 'fill_opacity',
            ],
            'classes': ('tab-style',),
        }),
        (None, {
            'fields': ['tooltip', 'popup'],
            'classes': ('tab-design',),
        }),
    ]

    def add_view(self, request, form_url='', extra_context=None):
        self.fieldsets = self.add_fieldsets
        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.fieldsets = self.edit_fieldsets
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def get_form(self, request, obj=None, **kwargs):
        defaults = {}
        if obj is None:
            defaults['form'] = GeoJsonLayerAddForm
        else:
            defaults['form'] = GeoJsonLayerChangeForm
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)

    def public_url(self, obj):
        text = '-'
        try:
            url = reverse('geojsonlayer', kwargs={'name': obj.name})
            text = format_html('<a href="{url}" target="_blank">{text}</a>', url=url, text=_('Url'))
        except Exception:
            pass
        return text
    public_url.short_description = 'PUBLIC URL'

    def view_layer(self, obj):
        text = '-'
        try:
            url = reverse('admin-api-geojsonlayer-detail', kwargs={'name': obj.name})
            text = format_html('<a href="{url}" target="_blank">{text}</a>', url=url, text=_('View Layer'))
        except Exception:
            pass
        return text
    view_layer.short_description = 'Layer'

    def save_model(self, request, obj, form, change):
        if not obj.service_path:
            unique_service_directory(obj)
        super(GeoJsonLayerAdmin, self).save_model(request, obj, form, change)
        if obj.url:
            messages.info(request, _('[%s] will be requested in background.') % obj.url)
        elif obj.data_file:
            messages.info(request, _('GeoJsonLayer will be generated/updated in background.'))
        force_refresh_data_file = False
        if 'force_refresh_data_file' in form.cleaned_data:
            force_refresh_data_file = form.cleaned_data['force_refresh_data_file']
        transaction.on_commit(
            lambda: async_geojsonlayer_refresh.delay(obj.pk, force_refresh_data_file)
        )


class DBLayerGroupInline(admin.TabularInline):
    model = DBLayerGroup
    extra = 0
    classes = ('tab-permissions',)
    verbose_name = _('Group')
    verbose_name_plural = _('Groups')


class DBLayerUserInline(admin.TabularInline):
    model = DBLayerUser
    extra = 0
    classes = ('tab-permissions',)
    verbose_name = _('User')
    verbose_name_plural = _('Users')


class DataBaseLayerFieldsInline(admin.TabularInline):
    model = DataBaseLayerField
    form = DataBaseLayerFieldsInlineForm
    extra = 0
    ordering = ('name',)

    can_delete = False
    fields = ('enabled', 'readonly', 'name', 'label', 'get_type', 'get_size', 'get_decimals', 'get_null', 'blank',
              'search', 'fullsearch', 'widget', 'widget_options',)
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


class DataBaseLayerVirtualFieldsInline(admin.TabularInline):
    model = DataBaseLayerVirtualField
    form = DataBaseLayerVirtualFieldsInlineForm
    extra = 0
    ordering = ('name',)
    can_delete = False
    fields = ('enabled', 'name', 'label', 'widget', 'widget_options',)
    classes = ('tab-virtual-fields',)


class DataBaseLayerReferencesInline(admin.TabularInline):
    model = DataBaseLayerReference
    extra = 0

    fields = ('service',)
    classes = ('tab-references',)


class DataBaseLayerStyleRuleInline(StyleRuleInlineMixin):
    model = DataBaseLayerStyleRule
    form = DataBaseLayerStyleRuleInlineForm


@admin.register(DataBaseLayer)
class DataBaseLayerAdmin(TabsMixin, admin.ModelAdmin):
    add_form_template = 'admin/layerserver/database_layer/add_form.html'
    change_form_template = 'admin/layerserver/database_layer/change_form.html'

    autocomplete_fields = ['category']
    list_display = ('has_geometry', 'name', 'table', 'db_connection', 'view_metadata', 'view_layer', 'public_url')
    list_display_links = ('name', 'table')
    list_filter = (('category', RelatedDropdownFilter), 'db_connection', 'visible_on_geoportal',
                   DataBaseLayerGeomNullFilter, 'shapetype')
    search_fields = ('name', 'title', 'keywords')
    inlines = []

    add_fieldsets = (
        ('Layer', {
            'fields': ('db_connection', 'geometry_columns', 'name', 'table', 'geom_field', 'srid', 'pk_field')
        }),
    )
    tabs = None
    edit_tabs = (
        (_('Information'), ('tab-information',)),
        (_('Data base'), ('tab-data-base',)),
        (_('Fields'), ('tab-fields',)),
        (_('Virtual Fields'), ('tab-virtual-fields',)),
        (_('Permissions'), ('tab-permissions',)),
        (_('Design'), ('tab-design',)),
    )

    edit_geom_tabs = (
        (_('Information'), ('tab-information',)),
        (_('Data base'), ('tab-data-base',)),
        (_('Fields'), ('tab-fields',)),
        (_('Virtual Fields'), ('tab-virtual-fields',)),
        (_('Style'), ('tab-style',)),
        (_('Permissions'), ('tab-permissions',)),
        (_('References'), ('tab-references',)),
        (_('Design'), ('tab-design',)),
    )

    edit_fieldsets = [
        (None, {
            'fields': [
                'category', 'name', 'title',
                'description', 'keywords', 'active',
                'visible_on_geoportal',
                ('allow_page_size_0', 'page_size', 'max_page_size',),
            ],
            'classes': ('tab-information',),
        }),
        (None, {
            'fields': [
                'db_connection', 'table', 'pk_field'
            ],
            'classes': ('tab-data-base',),
        }),
        ('Anonymous user', {
            'fields': [
                ('anonymous_view', 'anonymous_add', 'anonymous_update', 'anonymous_delete',)
            ],
            'classes': ('tab-permissions',),
        }),
        (None, {
            'fields': [
                'list_fields', 'form_fields',
            ],
            'classes': ('tab-design',),
        }),
    ]

    edit_geom_fieldsets = [
        (None, {
            'fields': [
                'category', 'name', 'title',
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
                'stroke_width', 'stroke_opacity', 'stroke_dash_array', 'fill_color', 'fill_opacity',
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
                'list_fields', 'form_fields', 'tooltip', 'popup'
            ],
            'classes': ('tab-design',),
        }),
    ]

    def has_geometry(self, obj):
        return obj.geom_field is not None
    has_geometry.boolean = True
    has_geometry.short_description = _('Has geometry')

    def public_url(self, obj):
        text = '-'
        try:
            url = reverse('content-list', kwargs={'name': obj.name})
            text = format_html('<a href="{url}" target="_blank">{text}</a>', url=url, text=_('Url'))
        except Exception:
            pass
        return text
    public_url.short_description = 'PUBLIC URL'

    def view_layer(self, obj):
        text = '-'
        try:
            url = reverse('admin-api-layer-content-list', kwargs={'name': obj.name})
            text = format_html('<a href="{url}" target="_blank">{text}</a>', url=url, text=_('View Layer'))
        except Exception:
            pass
        return text
    view_layer.short_description = 'LAYER'

    def view_metadata(self, obj):
        text = '-'
        try:
            url = reverse('admin-api-layer-detail', kwargs={'name': obj.name})
            text = format_html('<a href="{url}" target="_blank">{text}</a>', url=url, text=_('View Metadata'))
        except Exception:
            pass
        return text
    view_metadata.short_description = 'METADATA'

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('table', 'geom_field', 'srid', 'view_metadata', 'view_layer', 'public_url')
        return self.readonly_fields

    def add_view(self, request, form_url='', extra_context=None):
        self.fieldsets = self.add_fieldsets
        self.inlines = []
        return super(DataBaseLayerAdmin, self).add_view(
            request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.model.objects.get(pk=object_id)
        if obj.geom_field is not None:
            self.tabs = self.edit_geom_tabs
            self.fieldsets = self.edit_geom_fieldsets
            self.inlines = [DataBaseLayerFieldsInline, DataBaseLayerVirtualFieldsInline,
                            DBLayerUserInline, DBLayerGroupInline, DataBaseLayerReferencesInline,
                            DataBaseLayerStyleRuleInline]
        else:
            self.tabs = self.edit_tabs
            self.fieldsets = self.edit_fieldsets
            self.inlines = [DataBaseLayerFieldsInline, DataBaseLayerVirtualFieldsInline, DBLayerUserInline,
                            DBLayerGroupInline]
        conn_status = obj.db_connection.check_connection()
        if not conn_status:
            msg = 'ERROR: There was an error when connecting to: %s' % obj.db_connection
            messages.add_message(request, messages.ERROR, msg)
        extra_context = extra_context or {}
        widgets_templates = {}
        for k, v in list(widgets_types.items()):
            widgets_templates[k] = mark_safe(v.TEMPLATE.replace('\n', '\\n').replace('"', r'\"'))
        extra_context['widgets_templates'] = widgets_templates

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
        if '_addanother' not in request.POST and admin.options.IS_POPUP_VAR not in request.POST:
            request.POST = request.POST.copy()
            request.POST['_continue'] = 1
        return super().response_add(request, obj, post_url_continue)
