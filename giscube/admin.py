from functools import update_wrapper

from django.conf import settings
from django.contrib import admin
from django.db.models.functions import Concat
from django.http import JsonResponse
from django.urls import re_path
from django.utils.translation import gettext as _

from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from django_vue_tabs.admin import TabsMixin

from .admin_forms import DBConnectionForm
from .admin_mixins import MetadataInlineMixin
from .models import (Category, Dataset, DatasetGroupPermission, DatasetMetadata, DatasetUserPermission, DBConnection,
                     MetadataCategory, Resource, Server)


admin.site.site_title = settings.ADMIN_SITE_TITLE
admin.site.site_header = settings.ADMIN_SITE_HEADER
admin.site.index_title = settings.ADMIN_INDEX_TITLE


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    autocomplete_fields = ('parent',)
    fields = ('parent', 'name')
    list_display = ('__str__', 'parent', 'name', )
    list_display_links = ('__str__',)
    search_fields = ('name', 'parent__name')

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        queryset = queryset.prefetch_related('parent')
        queryset = queryset.annotate(custom_order=Concat('parent__name', 'name'))
        queryset = queryset.order_by('custom_order')
        return queryset, use_distinct

    def get_queryset(self, request):
        queryset = super().get_queryset(request).prefetch_related('parent')
        queryset = queryset.annotate(custom_order=Concat('parent__name', 'name'))
        queryset = queryset.order_by('custom_order')
        return queryset


@admin.register(DBConnection)
class DBConnectionAdmin(TabsMixin, admin.ModelAdmin):
    form = DBConnectionForm

    def get_urls(self):
        urls = super().get_urls()

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name

        my_urls = [
            re_path(r'(?P<id>\d+)/geometry_columns/$', wrap(self.geometry_columns),
                    name='%s_%s_geometry_columns' % info),
        ]

        return my_urls + urls

    def geometry_columns(self, request, id):
        data = []
        columns = self.model.objects.get(pk=id).geometry_columns()
        for column in columns:
            data.append(column)
        response = JsonResponse(data, safe=False)
        return response


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    pass


class ResourceInline(admin.StackedInline):
    model = Resource
    extra = 0
    classes = ('tab-resources',)


class DatasetMetadataInline(MetadataInlineMixin):
    model = DatasetMetadata


class DatasetGroupPermissionInline(admin.TabularInline):
    model = DatasetGroupPermission
    extra = 0
    classes = ('tab-permissions',)
    verbose_name = _('Group')
    verbose_name_plural = _('Groups')


class DatasetUserPermissionInline(admin.TabularInline):
    model = DatasetUserPermission
    extra = 0
    classes = ('tab-permissions',)
    verbose_name = _('User')
    verbose_name_plural = _('Users')


@admin.register(Dataset)
class DatasetAdmin(TabsMixin, admin.ModelAdmin):
    autocomplete_fields = ('category',)
    list_display = ('title',)
    inlines = (ResourceInline, DatasetGroupPermissionInline, DatasetUserPermissionInline, DatasetMetadataInline)
    list_filter = (('category', RelatedDropdownFilter), 'active')

    tabs = (
        (_('Information'), ('tab-information',)),
        (_('Options'), ('tab-options',)),
        (_('Design'), ('tab-design',)),
        (_('Resources'), ('tab-resources',)),
        (_('Permissions'), ('tab-permissions',)),
        (_('Metadata'), ('tab-metadata',)),
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
                'options'
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

    class Media:
        js = [
            'admin/js/jquery.init.js',
            'admin/js/giscube/dataset/change_view.js'
        ]


@admin.register(MetadataCategory)
class MetadataCategoryAdmin(admin.ModelAdmin):
    fields = ('code', 'name')
    list_display = ('code', 'name', )
    list_display_links = list_display
    search_fields = ('code', 'name')
