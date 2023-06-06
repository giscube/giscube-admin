from functools import update_wrapper

from tablib import Dataset as TablibDataset

from django.conf import settings
from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.db.models.functions import Concat
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import Context, Template
from django.urls import path, re_path, reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext as _

from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from django_vue_tabs.admin import TabsMixin

from .admin_forms import DBConnectionForm
from .admin_mixins import MetadataInlineMixin, ResourceAdminMixin
from .models import (BaseLayer, Category, Dataset, DatasetGroupPermission, DatasetMetadata, DatasetResource,
                     DatasetUserPermission, DBConnection, MapConfig, MapConfigBaseLayer, MetadataCategory, Server)


admin.site.site_title = settings.ADMIN_SITE_TITLE
admin.site.site_header = settings.ADMIN_SITE_HEADER
admin.site.index_title = settings.ADMIN_INDEX_TITLE


def get_reset_password_link(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk)),
    token = default_token_generator.make_token(user)
    url = reverse('password_reset_confirm', kwargs={'uidb64': uid[0], 'token': token})
    url = request.build_absolute_uri(url)
    return url


def csv_recover_password(modeladmin, request, queryset):
    headers = ('username', 'first_name', 'last_name', 'reset_password_link')
    data = TablibDataset(headers=headers)

    for user in queryset:
        data.append([
            user.username,
            user.first_name,
            user.last_name,
            get_reset_password_link(request, user)
        ])

    response = HttpResponse(data.export('csv'), 'text/csv')
    response['Content-Disposition'] = 'attachment; filename="users.csv"'
    return response


csv_recover_password.short_description = 'CSV per recuperació de contrasenyes'


def email_recover_password(modeladmin, request, queryset):
    context = {
        'users': queryset,
        'subject': settings.GISCUBE['password_recovery_email_subject'],
        'message': settings.GISCUBE['password_recovery_email_body']
    }

    return render(request, 'admin/giscube/recover_password/form.html', context)


email_recover_password.short_description = 'Email per recuperació de contrasenyes'


class UserAdmin(BaseUserAdmin):
    actions = list(BaseUserAdmin.actions) + [csv_recover_password, email_recover_password]

    def get_urls(self):
        urls = super().get_urls()

        my_urls = [
            path('send_recover_password', self.send_recover_password, name='send_recover_password'),
        ]

        return my_urls + urls

    def send_recover_password(self, request):
        users = request.POST.getlist('users')
        subject = request.POST['subject']
        email_from = settings.DEFAULT_FROM_EMAIL
        message = request.POST['message']
        template = Template(message)
        for user_id in users:
            user = User.objects.get(id=user_id)
            if user.email:
                activation_link = get_reset_password_link(request, user)
                context = {
                    'site_url': settings.SITE_URL,
                    'username': user.username,
                    'activation_link': activation_link,
                }
                render_context = Context(context)
                body = template.render(render_context)
                email = EmailMessage(subject, body, email_from, [user.email])
                email.send(fail_silently=False)

        return render(request, 'admin/giscube/recover_password/result.html', request.POST)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    autocomplete_fields = ('parent',)
    fields = ('parent', 'name', 'color')
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


class DatasetResourceInline(admin.StackedInline):
    model = DatasetResource
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
class DatasetAdmin(ResourceAdminMixin, TabsMixin, admin.ModelAdmin):
    autocomplete_fields = ('category',)
    list_display = ('title',)
    inlines = (DatasetResourceInline, DatasetGroupPermissionInline, DatasetUserPermissionInline, DatasetMetadataInline)
    list_filter = (('category', RelatedDropdownFilter), 'active')
    save_as = True

    tabs = (
        (_('Information'), ('tab-information',)),
        (_('Options'), ('tab-options',)),
        (_('Design'), ('tab-design',)),
        (_('Permissions'), ('tab-permissions',)),
        (_('Metadata'), ('tab-metadata',)),
        (_('Resources'), ('tab-resources',)),
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


@admin.register(MetadataCategory)
class MetadataCategoryAdmin(admin.ModelAdmin):
    fields = ('code', 'name')
    list_display = ('code', 'name', )
    list_display_links = list_display
    search_fields = ('code', 'name')


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('content_type',
                    'user',
                    'action_time',
                    'object_repr',
                    'accion',
                    )
    readonly_fields = ('content_type',
                       'user',
                       'action_time',
                       'object_id',
                       'object_repr',
                       'action_flag',
                       'change_message',
                       )
    list_filter = ('user', 'content_type',)
    date_hierarchy = 'action_time'

    def accion(self, obj):
        return str(obj)

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser and settings.GISCUBE_ENABLE_LOGENTRY

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class MapConfigBaseLayerInline(admin.TabularInline):
    model = MapConfigBaseLayer
    extra = 0
    verbose_name = _('Base layer')
    verbose_name_plural = _('Base layers')


@admin.register(MapConfig)
class MapConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'center_lat', 'center_lng', 'initial_zoom',)
    inlines = (MapConfigBaseLayerInline, )

    fieldsets = [
        (None, {
            'fields': ['name', 'title', 'description'],
        }),
        (_('Initial view'), {
            'fields': [
                ('center_lat', 'center_lng'), 'initial_zoom',
                'image',
                'configurations',
                'url',
                'visible',
                'active',
                'start',
                'type',
            ],
        }),
    ]


@admin.register(BaseLayer)
class BaseLayerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'properties')
    list_editable = ('name', 'properties')
