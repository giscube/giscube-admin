# -*- coding: utf-8 -*-


from django.contrib import admin
from django.db.models import F

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
    pass


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    pass
