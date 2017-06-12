from django.contrib import admin

from qgisserver.models import Service


class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title',)
    exclude = ('service_path',)
    search_fields = ('name', 'title',)

admin.site.register(Service, ServiceAdmin)
