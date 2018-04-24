from django.contrib import admin
from .models import Category

admin.site.site_title = 'GISCube Admin'
admin.site.site_header = 'GISCube'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', '__unicode__')
    search_fields = ('name', 'parent__name')
