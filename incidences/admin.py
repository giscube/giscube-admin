from django.contrib import admin

from leaflet.admin import LeafletGeoAdminMixin

from .models import Incidence


@admin.register(Incidence)
class IncidenceAdmin(LeafletGeoAdminMixin, admin.ModelAdmin):
    list_display = ("id", "title", "user", "email")
    search_fields = ("title", "user", "email")
