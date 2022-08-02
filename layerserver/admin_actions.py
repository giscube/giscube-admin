from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as _

from .tasks import async_geojsonlayer_refresh


def geojsonlayer_force_refresh_data(modeladmin, request, queryset):
    if not request.user.has_perm('layerserver.change_geojsonlayer'):
        raise PermissionDenied

    for obj in queryset.all():
        async_geojsonlayer_refresh.delay(obj.pk, True)
    n = queryset.count()
    modeladmin.message_user(request, _('Forcing refresh of %s geojsonlayers') % n, messages.INFO)


geojsonlayer_force_refresh_data.short_description = _('Force refresh data files')
