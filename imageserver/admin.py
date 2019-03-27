from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html

from imageserver.models import Service, Layer, ServiceLayer, NamedMask


class ServiceLayerInline(admin.TabularInline):
    model = ServiceLayer
    extra = 0


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    autocomplete_fields = ('category',)
    list_display = ('title', 'url_wms')
    search_fields = ('title',)
    exclude = ('service_path',)
    readonly_fields = ('extent',)
    inlines = (ServiceLayerInline,)

    def url_wms(self, obj):
        return format_html('<a target="_blank" href="{0}/imageserver/services/{1}">WMS URL {1}</a>',
                           settings.GISCUBE_URL, obj.name)
    url_wms.short_description = 'WMS URL'


@admin.register(Layer)
class LayerAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)
    exclude = ('layer_path', 'mask_path')


@admin.register(NamedMask)
class NamedMaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'projection')
    search_fields = ('name',)
    exclude = ('mask_path',)
