# -*- coding: utf-8 -*-


from django.contrib import admin

from django_vue_tabs.admin import TabsMixin

from .models import Category, DBConnection, Server


admin.site.site_title = 'GISCube Admin'
admin.site.site_header = 'GISCube'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', '__str__')
    search_fields = ('name', 'parent__name')


@admin.register(DBConnection)
class DBConnectionAdmin(TabsMixin, admin.ModelAdmin):
    pass


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    pass
