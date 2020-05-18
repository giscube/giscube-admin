from django.contrib import admin, messages
from django.db import transaction
from django.urls import resolve, reverse
from django.utils.html import format_html, mark_safe
from django.utils.translation import gettext as _

from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from django_vue_tabs.admin import TabsMixin

from giscube.admin_mixins import MetadataInlineMixin
from giscube.utils import unique_service_directory

from .admin_actions import geojsonlayer_force_refresh_data
from .admin_filters import DataBaseLayerGeomNullFilter
from .admin_forms import (DataBaseLayerAddForm, DataBaseLayerChangeForm, DataBaseLayerFieldsInlineForm,
                          DataBaseLayerReferencesInlineForm, DataBaseLayerStyleRuleInlineForm,
                          DataBaseLayerVirtualFieldsInlineForm, GeoJsonLayerAddForm, GeoJsonLayerChangeForm,
                          GeoJsonLayerStyleRuleInlineForm)
from .models import (DataBaseLayer, DataBaseLayerField, DataBaseLayerMetadata, DataBaseLayerReference,
                     DataBaseLayerStyleRule, DataBaseLayerVirtualField, DBLayerGroup, DBLayerUser, GeoJsonLayer,
                     GeoJsonLayerGroupPermission, GeoJsonLayerMetadata, GeoJsonLayerStyleRule,
                     GeoJsonLayerUserPermission)
from .tasks import async_geojsonlayer_refresh
from .widgets import widgets_types


class StyleRuleInlineMixin(admin.StackedInline):
    model = GeoJsonLayerStyleRule
    extra = 0
    classes = ('tab-style',)
    fields = ('order', ('field', 'comparator', 'value'), ('icon_type', 'icon', 'icon_color'),
              'shape_radius', ('stroke_color', 'stroke_width', 'stroke_opacity', 'stroke_dash_array'),
              ('fill_color', 'fill_opacity'))
    verbose_name = _('Rule')
    verbose_name_plural = _('Rules')


class GeoJsonGroupPermissionsInline(admin.TabularInline):
    model = GeoJsonLayerGroupPermission
    extra = 0
    classes = ('tab-permissions',)
    verbose_name = _('Group')
    verbose_name_plural = _('Groups')


class GeoJsonUserPermissionsInline(admin.TabularInline):
    model = GeoJsonLayerUserPermission
    extra = 0
    classes = ('tab-permissions',)
    verbose_name = _('User')
    verbose_name_plural = _('Users')


class GeoJsonLayerMetadataInline(MetadataInlineMixin):
    model = GeoJsonLayerMetadata


class GeoJsonLayerStyleRuleInline(StyleRuleInlineMixin):
    model = GeoJsonLayerStyleRule
    form = GeoJsonLayerStyleRuleInlineForm


@admin.register(GeoJsonLayer)
class GeoJsonLayerAdmin(TabsMixin, admin.ModelAdmin):
    add_form_template = 'admin/layerserver/geojson_layer/add_form.html'
    change_form_template = 'admin/layerserver/geojson_layer/change_form.html'
    autocomplete_fields = ('category', 'design_from',)
    list_display = ('name', 'title', 'view_layer', 'public_url')
    list_filter = (('category', RelatedDropdownFilter), 'visible_on_geoportal', 'shapetype')
    search_fields = ('name', 'title', 'keywords')
    readonly_fields = ('last_fetch_on', 'generated_on', 'view_layer', 'public_url')
    inlines = [
        GeoJsonLayerStyleRuleInline, GeoJsonLayerMetadataInline, GeoJsonGroupPermissionsInline,
        GeoJsonUserPermissionsInline
    ]
    actions = admin.ModelAdmin.actions + [geojsonlayer_force_refresh_data]
    save_as = True

    tabs_add = (
        (_('Information'), ('tab-information',)),
        (_('GeoJSON'), ('tab-geojson',)),
        (_('Style'), ('tab-style',)),
        (_('Design'), ('tab-design',)),
        (_('Permissions'), ('tab-permissions',)),
        (_('Metadata'), ('tab-metadata',)),
    )

    tabs_edit = (
        (_('Information'), ('tab-information',)),
        (_('GeoJSON'), ('tab-geojson',)),
        (_('Style'), ('tab-style',)),
        (_('Design'), ('tab-design',)),
        (_('Permissions'), ('tab-permissions',)),
        (_('Metadata'), ('tab-metadata',)),
        (_('Task log'), ('tab-log',)),
    )

    add_fieldsets = [
        (None, {
            'fields': [
                'category', 'name', 'title',
                'description', 'keywords', 'active', 'visible_on_geoportal',
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
                'shapetype', 'icon_type', 'icon', 'icon_color', 'shape_radius', 'stroke_color',
                'stroke_width', 'stroke_opacity', 'stroke_dash_array', 'fill_color', 'fill_opacity',
            ],
            'classes': ('tab-style',),
        }),
        (None, {
            'fields': ['design_from'],
            'classes': ('tab-design',),
        }),
        ('Design', {
            'fields': ['tooltip', 'generate_popup', 'popup', 'legend'],
            'classes': ('tab-design',),
        }),
        (_('Cluster'), {
            'fields': ['cluster_enabled', 'cluster_options'],
            'classes': ('tab-design',),
        }),
        (_('Basic permissions'), {
            'fields': [
                'anonymous_view', 'authenticated_user_view',
            ],
            'classes': ('tab-permissions',),
        }),
    ]

    edit_fieldsets = [
        (None, {
            'fields': [
                'category', 'name', 'title',
                'description', 'keywords', 'active', 'visible_on_geoportal',
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
                'shapetype', 'icon_type', 'icon', 'icon_color', 'shape_radius', 'stroke_color',
                'stroke_width', 'stroke_opacity', 'stroke_dash_array', 'fill_color', 'fill_opacity',
            ],
            'classes': ('tab-style',),
        }),
        (None, {
            'fields': ['design_from'],
            'classes': ('tab-design',),
        }),
        ('Design', {
            'fields': ['tooltip', 'generate_popup', 'popup', 'legend'],
            'classes': ('tab-design',),
        }),
        (_('Cluster'), {
            'fields': ['cluster_enabled', 'cluster_options'],
            'classes': ('tab-design',),
        }),
        (_('Basic permissions'), {
            'fields': [
                'anonymous_view', 'authenticated_user_view',
            ],
            'classes': ('tab-permissions',),
        }),
    ]
    ordering = ['name']

    def add_view(self, request, form_url='', extra_context=None):
        self.tabs = self.tabs_add
        self.fieldsets = self.add_fieldsets
        extra_context = extra_context or {}
        extra_context['can_apply_style'] = True
        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.tabs = self.tabs_edit
        self.fieldsets = self.edit_fieldsets
        obj = self.model.objects.filter(pk=object_id).first()
        extra_context = extra_context or {}
        extra_context['view_layer'] = self.view_layer(obj)
        extra_context['can_apply_style'] = True
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def get_form(self, request, obj=None, **kwargs):
        defaults = {}
        if obj is None:
            defaults['form'] = GeoJsonLayerAddForm
        else:
            defaults['form'] = GeoJsonLayerChangeForm
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        current_url = resolve(request.path_info).url_name
        if current_url == 'layerserver_geojsonlayer_autocomplete':
            queryset = queryset.filter(design_from__isnull=True)
        return queryset, use_distinct

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

        force_refresh_data_file = form.cleaned_data.get('force_refresh_data_file', False)
        generate_popup = form.cleaned_data.get('generate_popup', False)
        if not force_refresh_data_file and generate_popup:
            obj.popup = obj.get_default_popup()

        super(GeoJsonLayerAdmin, self).save_model(request, obj, form, change)

        if obj.url:
            messages.info(request, _('[%s] will be requested in background.') % obj.url)
        elif obj.data_file:
            messages.info(request, _('GeoJsonLayer will be generated/updated in background.'))

        transaction.on_commit(
            lambda: async_geojsonlayer_refresh.delay(obj.pk, force_refresh_data_file, generate_popup)
        )


class DBLayerMetadataInline(MetadataInlineMixin):
    model = DataBaseLayerMetadata


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
    fields = ('enabled', 'name', 'label', 'widget', 'widget_options',)
    classes = ('tab-virtual-fields',)


class DataBaseLayerReferencesInline(admin.TabularInline):
    autocomplete_fields = ('service',)
    model = DataBaseLayerReference
    form = DataBaseLayerReferencesInlineForm
    extra = 0

    fields = ('service', 'format', 'transparent', 'refresh',)
    classes = ('tab-references',)


class DataBaseLayerStyleRuleInline(StyleRuleInlineMixin):
    model = DataBaseLayerStyleRule
    form = DataBaseLayerStyleRuleInlineForm


@admin.register(DataBaseLayer)
class DataBaseLayerAdmin(TabsMixin, admin.ModelAdmin):
    add_form_template = 'admin/layerserver/database_layer/add_form.html'
    change_form_template = 'admin/layerserver/database_layer/change_form.html'

    autocomplete_fields = ['category']
    list_display = ('has_geometry', 'name', 'title', 'table', 'db_connection', 'view_metadata', 'view_layer',
                    'public_url')
    list_display_links = ('name', 'title', 'table')
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
        (_('Design'), ('tab-design',)),
        (_('Permissions'), ('tab-permissions',)),
        (_('Metadata'), ('tab-metadata',)),
    )

    edit_geom_tabs = (
        (_('Information'), ('tab-information',)),
        (_('Data base'), ('tab-data-base',)),
        (_('Fields'), ('tab-fields',)),
        (_('Virtual Fields'), ('tab-virtual-fields',)),
        (_('Style'), ('tab-style',)),
        (_('Design'), ('tab-design',)),
        (_('References'), ('tab-references',)),
        (_('Permissions'), ('tab-permissions',)),
        (_('Metadata'), ('tab-metadata',)),
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
        ('Anonymous users', {
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
        })
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
                'shapetype', 'icon_type', 'icon', 'icon_color', 'shape_radius', 'stroke_color',
                'stroke_width', 'stroke_opacity', 'stroke_dash_array', 'fill_color', 'fill_opacity',
            ],
            'classes': ('tab-style',),
        }),
        ('Anonymous users', {
            'fields': [
                ('anonymous_view', 'anonymous_add', 'anonymous_update', 'anonymous_delete',)
            ],
            'classes': ('tab-permissions',),
        }),
        (None, {
            'fields': ['wms_as_reference'],
            'classes': ('tab-references',),
        }),
        (None, {
            'fields': [
                'list_fields', 'form_fields', 'tooltip', 'popup', 'legend'
            ],
            'classes': ('tab-design',),
        }),
    ]
    ordering = ['name']

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
                            DataBaseLayerStyleRuleInline, DBLayerMetadataInline]
        else:
            self.tabs = self.edit_tabs
            self.fieldsets = self.edit_fieldsets
            self.inlines = [DataBaseLayerFieldsInline, DataBaseLayerVirtualFieldsInline, DBLayerUserInline,
                            DBLayerGroupInline, DBLayerMetadataInline, DBLayerMetadataInline]
        conn_status = obj.db_connection.check_connection()
        if not conn_status:
            msg = 'ERROR: There was an error when connecting to: %s' % obj.db_connection
            messages.add_message(request, messages.ERROR, msg)
        extra_context = extra_context or {}
        widgets_templates = {}
        for k, v in list(widgets_types.items()):
            widgets_templates[k] = mark_safe(v.TEMPLATE.replace('\n', '\\n').replace('"', r'\"'))
        extra_context['widgets_templates'] = widgets_templates
        extra_context['view_metadata'] = self.view_metadata(obj)
        extra_context['view_layer'] = self.view_layer(obj)
        extra_context['can_apply_style'] = obj.geom_field is not None

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
