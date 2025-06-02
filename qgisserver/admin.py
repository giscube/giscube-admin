import logging
import os
import shutil
import zipfile

from django.conf import settings
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db.models import Value as V
from django.db.models.functions import Coalesce, Concat
from django.urls import resolve
from django.utils.html import format_html
from django.utils.translation import gettext as _

from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from django_vue_tabs.admin import TabsMixin

from giscube.utils import get_wms_layers
from giscube.admin_mixins import MetadataInlineMixin, ResourceAdminMixin
from giscube.tilecache.admin_mixins import TileCacheModelAdminMixin

from .admin_forms import ServiceChangeForm, ServiceFilterForm
from .models import (Project, Service, ServiceGroupPermission, ServiceMetadata, ServiceResource, ServiceUserPermission,
                     ServiceFilter, project_unique_service_directory)
from .signals import service_project_updated, service_updated
from .utils import unique_service_directory


db_logger = logging.getLogger('db')


class ServiceMetadataInline(MetadataInlineMixin):
    model = ServiceMetadata


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class ServiceResourceInline(admin.StackedInline):
    model = ServiceResource
    extra = 0
    classes = ('tab-resources',)


class ServiceGroupPermissionInline(admin.TabularInline):
    model = ServiceGroupPermission
    extra = 0
    classes = ('tab-permissions',)
    verbose_name = _('Group')
    verbose_name_plural = _('Groups')


class ServiceUserPermissionInline(admin.TabularInline):
    model = ServiceUserPermission
    extra = 0
    classes = ('tab-permissions',)
    verbose_name = _('User')
    verbose_name_plural = _('Users')


class ServiceFilterInline(admin.StackedInline):
    model = ServiceFilter
    form = ServiceFilterForm
    extra = 0
    classes = ('tab-options',)
    verbose_name = _('WMS Filter')
    verbose_name_plural = _('WMS Filters')

class ServiceAdmin(TileCacheModelAdminMixin, ResourceAdminMixin, TabsMixin, admin.ModelAdmin):
    change_form_template = 'admin/qgisserver/service/change_form.html'
    form = ServiceChangeForm
    autocomplete_fields = ('category',)
    list_display = ('name', 'title', 'url_wms', 'anonymous_view_user', 'visible_on_geoportal',)
    list_filter = (('category', RelatedDropdownFilter), ('project', RelatedDropdownFilter),
                   'visible_on_geoportal')
    exclude = ('service_path',)
    search_fields = ('name', 'title', 'keywords')
    filter_horizontal = ('servers',)
    inlines = (
        ServiceMetadataInline,
        ServiceResourceInline,
        ServiceGroupPermissionInline,
        ServiceUserPermissionInline,
        ServiceFilterInline
    )
    readonly_fields = ('project_file', 'layers')
    save_as = True

    tabs = (
        (_('Information'), ('tab-information',)),
        (_('Options'), ('tab-options',)),
        (_('Design'), ('tab-design',)),
        (_('Permissions'), ('tab-permissions',)),
        (_('Metadata'), ('tab-metadata',)),
        (_('Resources'), ('tab-resources',)),

        (_('Tile Cache'), ('tab-tilecache',)),
        (_('Servers'), ('tab-servers',)),
    )

    fieldsets = [
        (None, {
            'fields': [
                'category', 'name', 'title',
                'description', 'keywords', 'active', 'visible_on_geoportal',
                'project',
                'project_file'
            ],
            'classes': ('tab-information',),
        }),
        (None, {
            'fields': [
                'wms_single_image', 'wms_buffer_enabled', 'wms_buffer_size', 'wms_tile_sizes',
                'wms_getfeatureinfo_enabled',
                'options', "layers"
            ],
            'classes': ('tab-options',),
        }),
        (None, {
            'fields': [
                'popup',
                'legend',
            ],
            'classes': ('tab-design',),
        }),
        (None, {
            'fields': [
                'servers',
            ],
            'classes': ('tab-servers',),
        }),
        (_('Basic permissions'), {
            'fields': [
                'anonymous_view',
                'anonymous_write',
                'authenticated_user_view',
                'authenticated_user_write',
            ],
            'classes': ('tab-permissions',),
        }),
    ]

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.model.objects.filter(pk=object_id).first()
        extra_context = {} if extra_context is None else extra_context
        extra_context['all_layers'] = obj.layers.split(',') if obj.layers else None
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

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
        return format_html('<a target="_blank" href="{0}">View WMS URL {1}</a>', url, obj.name)
    url_wms.short_description = 'WMS URL'

    def anonymous_view_user(self, obj):
       return obj.anonymous_view
    anonymous_view_user.short_description = _('Anonymous view')
    anonymous_view_user.boolean = True

    def update_layers(self, request, obj):
        if obj.service_internal_url:
            try:
                obj.layers = get_wms_layers(obj.service_internal_url)
                obj.save()
            except ValidationError as e:
                error_message = str(e)
                
                messages.error(request, error_message)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if form.is_valid() and 'project' in form.changed_data:
            try:
                if not obj.service_path:
                    unique_service_directory(obj)
                mapdata_path = os.path.join(obj.service_path, 'mapdata')
                mapdata_dir = os.path.join(settings.MEDIA_ROOT, mapdata_path)
                if obj.project_file and obj.project_file.name and not obj.project_file.name.startswith(mapdata_path):
                    os.remove(os.path.join(settings.MEDIA_ROOT, obj.project_file.name))
                if os.path.exists(mapdata_dir):
                    shutil.rmtree(mapdata_dir)
                os.mkdir(mapdata_dir)
                if form.cleaned_data['project'].name.lower().endswith('.zip'):
                    zip_file = zipfile.ZipFile(form.cleaned_data['project'].file)
                    zip_file.extractall(mapdata_dir)
                    name = '%s.qgs' % obj.name
                    obj.project_file.name = project_unique_service_directory(obj, name)
                else:
                    name = form.cleaned_data['project'].name
                    file = ContentFile(form.cleaned_data['project'].file.getvalue())
                    obj.project_file.save(name, file, save=True)
                obj.save()
                self.update_layers(request, obj)
            except Exception as e:
                db_logger.exception(e)
                messages.error(request, _('Is not possible to save %s' % form.cleaned_data['project'].name))
            else:
                # FIXME: remove signals usage
                service_project_updated.send(sender=self.__class__, obj=obj)

        if form.is_valid():
            # FIXME: remove signals usage
            service_updated.send(sender=self.__class__, obj=obj)


if not settings.GISCUBE_GIS_SERVER_DISABLED:
    admin.site.register(Project, ProjectAdmin)
    admin.site.register(Service, ServiceAdmin)
