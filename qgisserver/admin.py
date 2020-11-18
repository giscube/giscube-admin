from django.conf import settings
from django.contrib import admin
from django.db.models import Value as V
from django.db.models.functions import Coalesce, Concat
from django.urls import resolve
from django.utils.html import format_html
from django.utils.translation import gettext as _

from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from django_vue_tabs.admin import TabsMixin

from giscube.admin_mixins import MetadataInlineMixin, ResourceAdminMixin
from giscube.tilecache.admin_mixins import TileCacheModelAdminMixin

from .admin_forms import ServiceChangeForm
from .models import Project, Service, ServiceMetadata, ServiceResource


class ServiceMetadataInline(MetadataInlineMixin):
    model = ServiceMetadata


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class ServiceResourceInline(admin.StackedInline):
    model = ServiceResource
    extra = 0
    classes = ('tab-resources',)


class ServiceAdmin(TileCacheModelAdminMixin, ResourceAdminMixin, TabsMixin, admin.ModelAdmin):
    change_form_template = 'admin/qgisserver/service/change_form.html'

    form = ServiceChangeForm

    autocomplete_fields = ('category',)
    list_display = ('title', 'url_wms', 'visibility', 'visible_on_geoportal',)
    list_filter = (('category', RelatedDropdownFilter), ('project', RelatedDropdownFilter), 'visibility',
                   'visible_on_geoportal')
    exclude = ('service_path', 'active')
    search_fields = ('name', 'title', 'keywords')
    filter_horizontal = ('servers',)
    inlines = (ServiceMetadataInline, ServiceResourceInline,)

    tabs = (
        (_('Information'), ('tab-information',)),
        (_('Options'), ('tab-options',)),
        (_('Design'), ('tab-design',)),
        (_('Metadata'), ('tab-metadata',)),
        (_('Resources'), ('tab-resources',)),

        (_('Tile Cache'), ('tab-tilecache',)),
        (_('Servers'), ('tab-servers',)),
    )

    fieldsets = [
        (None, {
            'fields': [
                'category', 'name', 'title',
                'description', 'keywords', 'visibility', 'visible_on_geoportal',
                'project_file'
            ],
            'classes': ('tab-information',),
        }),
        (None, {
            'fields': [
                'wms_buffer_enabled', 'wms_buffer_size', 'wms_tile_sizes', 'options'
            ],
            'classes': ('tab-options',),
        }),
        (None, {
            'fields': [
                'legend',
            ],
            'classes': ('tab-design',),
        }),
        (None, {
            'fields': [
                'servers',
            ],
            'classes': ('tab-servers',),
        })
    ]

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        current_url = resolve(request.path_info).url_name
        if current_url == 'qgisserver_service_autocomplete':
            queryset = queryset.annotate(custom_order=Concat('title', 'name'))
            queryset = queryset.order_by('custom_order')
        return queryset, use_distinct

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        current_url = resolve(request.path_info).url_name
        if current_url == 'qgisserver_service_autocomplete':
            queryset = queryset.annotate(custom_order=Concat(Coalesce('title', V('')), 'name'))
            queryset = queryset.order_by('custom_order')
        return queryset

    def url_wms(self, obj):
        url = '%s?service=WMS&version=1.1.1&request=GetCapabilities' % obj.service_url
        return format_html('<a target="_blank" href="{0}">WMS URL {1}</a>', url, obj.name)
    url_wms.short_description = 'WMS URL'


if not settings.GISCUBE_GIS_SERVER_DISABLED:
    admin.site.register(Project, ProjectAdmin)
    admin.site.register(Service, ServiceAdmin)
