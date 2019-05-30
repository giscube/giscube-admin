from django.contrib import admin

from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter

from geoportal.models import Dataset, Resource


class ResourceInline(admin.StackedInline):
    model = Resource
    extra = 0


class DatasetAdmin(admin.ModelAdmin):
    autocomplete_fields = ('category',)
    list_display = ('title',)
    inlines = (ResourceInline,)
    list_filter = (('category', RelatedDropdownFilter), 'active')


admin.site.register(Dataset, DatasetAdmin)
