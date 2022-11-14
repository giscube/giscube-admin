from django.contrib import admin

from django_admin_listfilter_dropdown.filters import DropdownFilter
from rangefilter.filter import DateRangeFilter

from .models import VisorUserTrack


@admin.register(VisorUserTrack)
class VisorUserTrackAdmin(admin.ModelAdmin):
    list_display = ['username', 'ip', 'datetime']
    readonly_fields = ['username', 'ip', 'datetime']
    search_fields = ['username']
    list_filter = [
        ('datetime', DateRangeFilter),
        ('username', DropdownFilter)
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
