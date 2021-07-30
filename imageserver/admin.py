from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext as _

from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from django_vue_tabs.admin import TabsMixin

from giscube.admin_mixins import MetadataInlineMixin, ResourceAdminMixin
from giscube.tilecache.admin_mixins import TileCacheModelAdminMixin

from .admin_forms import ServiceChangeForm
from .models import (Layer, NamedMask, Service, ServiceGroupPermission, ServiceLayer, ServiceMetadata, ServiceResource,
                     ServiceUserPermission)


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


class ServiceGroupPermissionsInline(admin.TabularInline):
    model = ServiceGroupPermission
    extra = 0
    classes = ('tab-permissions',)
    verbose_name = _('Group')
    verbose_name_plural = _('Groups')


class ServiceUserPermissionsInline(admin.TabularInline):
    model = ServiceUserPermission
    extra = 0
    classes = ('tab-permissions',)
    verbose_name = _('User')
    verbose_name_plural = _('Users')


class ServiceAdmin(TileCacheModelAdminMixin, ResourceAdminMixin, TabsMixin, admin.ModelAdmin):
    change_form_template = 'admin/imageserver/service/change_form.html'
    form = ServiceChangeForm
    autocomplete_fields = ('category',)
    list_display = ('title', 'url_wms')
    list_filter = (('category', RelatedDropdownFilter), 'visible_on_geoportal')
    search_fields = ('title',)
    readonly_fields = ('extent',)
    inlines = (
        ServiceLayerInline, ServiceMetadataInline, ServiceResourceInline,
        ServiceGroupPermissionsInline,
        ServiceUserPermissionsInline
    )
    tabs = (
        (_('Information'), ('tab-information',)),
        (_('Options'), ('tab-options',)),
        (_('Layers'), ('tab-layers',)),
        (_('Design'), ('tab-design',)),
        (_('Permissions'), ('tab-permissions',)),
        (_('Metadata'), ('tab-metadata',)),
        (_('Resources'), ('tab-resources',)),
        (_('Tile Cache'), ('tab-tilecache',)),
    )

    fieldsets = [
        (None, {
            'fields': [
                'category', 'name', 'title',
                'description', 'keywords', 'active', 'visible_on_geoportal'
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
        (_('Basic permissions'), {
            'fields': [
                'anonymous_view', 'authenticated_user_view',
            ],
            'classes': ('tab-permissions',),
        }),
    ]

    def url_wms(self, obj):
        url = '%s?service=WMS&version=1.1.1&request=GetCapabilities' % obj.service_url
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
