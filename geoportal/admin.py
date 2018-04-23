from django.contrib import admin

from geoportal.models import Dataset, Resource


class ResourceInline(admin.StackedInline):
    model = Resource
    extra = 0


class DatasetAdmin(admin.ModelAdmin):
    list_display = ('title',)
    inlines = (ResourceInline,)


admin.site.register(Dataset, DatasetAdmin)
