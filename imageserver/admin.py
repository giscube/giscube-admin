from django.contrib import admin
from django.conf import settings

from imageserver.models import Service, Layer, ServiceLayer, NamedMask


class ServiceLayerInline(admin.TabularInline):
    model = ServiceLayer
    extra = 0


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'url_wms')
    search_fields = ('title',)
    exclude = ('service_path',)
    readonly_fields = ('extent',)
    inlines = (ServiceLayerInline,)

    def url_wms(self, obj):
        return '<a target="_blank" href="%s/imageserver/services/%s">WMS URL %s</a>' % (
            settings.GISCUBE_URL, obj.name, obj.name)
    url_wms.allow_tags = True
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
