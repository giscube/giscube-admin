from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html

from qgisserver.models import Project, Service


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class ServiceAdmin(admin.ModelAdmin):
    autocomplete_fields = ('category',)
    list_display = ('title', 'url_wms')
    exclude = ('service_path', 'active')
    search_fields = ('name', 'title', 'keywords')
    filter_horizontal = ('servers',)

    def url_wms(self, obj):
        return format_html('<a target="_blank" href="{0}/qgisserver/services/{1}">WMS URL {1}</a>',
                           settings.GISCUBE_URL, obj.name)
    url_wms.short_description = 'WMS URL'


admin.site.register(Service, ServiceAdmin)
