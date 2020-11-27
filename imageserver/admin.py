from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext as _

from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from django_vue_tabs.admin import TabsMixin

from giscube.admin_mixins import MetadataInlineMixin, ResourceAdminMixin
from giscube.utils import url_slash_join
from imageserver.models import Layer, NamedMask, Service, ServiceLayer, ServiceMetadata, ServiceResource


class ServiceLayerInline(admin.TabularInline):
    model = ServiceLayer
    extra = 0
    classes = ('tab-layers',)

class ServiceMetadataInline(MetadataInlineMixin):
    model = ServiceMetadata


class ServiceResourceInline(admin.StackedInline):
    model = ServiceResource
    extra = 0
    classes = ('tab-resources',)


class ServiceAdmin(ResourceAdminMixin, TabsMixin, admin.ModelAdmin):
    autocomplete_fields = ('category',)
    list_display = ('title', 'url_wms')
    list_filter = (('category', RelatedDropdownFilter), 'visibility', 'visible_on_geoportal')
    search_fields = ('title',)
    readonly_fields = ('extent',)
    inlines = (ServiceLayerInline, ServiceMetadataInline, ServiceResourceInline,)

    tabs = (
        (_('Information'), ('tab-information',)),
        (_('Options'), ('tab-options',)),
        (_('Layers'), ('tab-layers',)),
        (_('Design'), ('tab-design',)),
        (_('Metadata'), ('tab-metadata',)),
        (_('Resources'), ('tab-resources',)),
    )

    fieldsets = [
        (None, {
            'fields': [
                'category', 'name', 'title',
                'description', 'keywords', 'active', 'visibility', 'visible_on_geoportal'
            ],
            'classes': ('tab-information',),
        }),
        (None, {
            'fields': [
                'wms_single_image', 'projection', 'supported_srs', 'extent', 'options'
            ],
            'classes': ('tab-options',),
        }),
        (None, {
            'fields': [
                'legend',
            ],
            'classes': ('tab-design',),
        }),
    ]

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
