from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html

from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter

from giscube.utils import url_slash_join
from imageserver.models import Layer, NamedMask, Service, ServiceLayer


class ServiceLayerInline(admin.TabularInline):
    model = ServiceLayer
    extra = 0


class ServiceAdmin(admin.ModelAdmin):
    autocomplete_fields = ('category',)
    list_display = ('title', 'url_wms')
    list_filter = (('category', RelatedDropdownFilter), 'visibility', 'visible_on_geoportal')
    search_fields = ('title',)
    exclude = ('service_path',)
    readonly_fields = ('extent',)
    inlines = (ServiceLayerInline,)

    def url_wms(self, obj):
        url = url_slash_join(settings.GISCUBE_URL, '/imageserver/services/%s' % obj.name)
        return format_html('<a target="_blank" href="{0}">WMS URL {1}</a>', url, obj.name)
    url_wms.short_description = 'WMS URL'


class LayerAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)
    exclude = ('layer_path', 'mask_path')


class NamedMaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'projection')
    search_fields = ('name',)
    exclude = ('mask_path',)


if not settings.GISCUBE_IMAGE_SERVER_DISABLED:
    admin.site.register(Service, ServiceAdmin)
    admin.site.register(Layer, LayerAdmin)
    admin.site.register(NamedMask, NamedMaskAdmin)
