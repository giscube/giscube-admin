from django.contrib import admin

from geoportal.models import Category, Dataset, Resource


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', '__unicode__')
    search_fields = ('name', 'parent__name')


class ResourceInline(admin.StackedInline):
    model = Resource
    extra = 0


class DatasetAdmin(admin.ModelAdmin):
    list_display = ('title',)
    inlines = (ResourceInline,)

admin.site.register(Dataset, DatasetAdmin)
