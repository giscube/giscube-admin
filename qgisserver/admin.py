from django.contrib import admin
from django.conf import settings

from qgisserver.models import Service


class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'url_wms')
    exclude = ('service_path',)
    search_fields = ('name', 'title', 'keywords')

    def url_wms(self, obj):
        return '<a target="_blank" href="%s/qgisserver/services/%s">WMS URL %s</a>' % (
            settings.GISCUBE_URL, obj.name, obj.name)
    url_wms.allow_tags = True
    url_wms.short_description = 'WMS URL'


admin.site.register(Service, ServiceAdmin)
