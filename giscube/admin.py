# -*- coding: utf-8 -*-

from functools import update_wrapper

from django.contrib import admin
from django.db.models import F
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.urls import re_path

from django_vue_tabs.admin import TabsMixin

from .models import Category, DBConnection, Server


admin.site.site_title = 'GISCube Admin'
admin.site.site_header = 'GISCube'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    autocomplete_fields = ('parent',)
    list_display = ('name', 'parent', '__str__')
    search_fields = ('name', 'parent__name')

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        queryset = queryset.order_by(F('parent__name').desc(nulls_last=False), 'name')
        return queryset, use_distinct

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.order_by(F('parent__name').desc(nulls_last=False), 'name')
        return qs


@admin.register(DBConnection)
class DBConnectionAdmin(TabsMixin, admin.ModelAdmin):

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
