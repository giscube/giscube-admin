from django.conf import settings
from django.contrib import admin
from django.db.models import Value as V
from django.db.models.functions import Coalesce, Concat
from django.urls import resolve
from django.utils.html import format_html

from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter

from giscube.utils import url_slash_join
from qgisserver.models import Project, Service


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class ServiceAdmin(admin.ModelAdmin):
    autocomplete_fields = ('category',)
    list_display = ('title', 'url_wms')
    list_filter = (('category', RelatedDropdownFilter), ('project', RelatedDropdownFilter), 'visibility',
                   'visible_on_geoportal')
    exclude = ('service_path', 'active')
    search_fields = ('name', 'title', 'keywords')
    filter_horizontal = ('servers',)

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
        url = url_slash_join(settings.GISCUBE_URL, '/qgisserver/services/%s' % obj.name)
        return format_html('<a target="_blank" href="{0}">WMS URL {1}</a>', url, obj.name)
    url_wms.short_description = 'WMS URL'


if not settings.GISCUBE_GIS_SERVER_DISABLED:
    admin.site.register(Project, ProjectAdmin)
    admin.site.register(Service, ServiceAdmin)
