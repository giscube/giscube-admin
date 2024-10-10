from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext as _


from giscube.tilecache.caches import GiscubeServiceCache
from giscube.utils import get_service_wms_bbox, remove_app_url, url_slash_join


class TileCacheModelAdminMixin:
    def get_fieldsets(self, request, obj=None):
        if obj:
            obj._request = request

        fieldsets = list(self.fieldsets)
        if obj:
            fieldsets.append(
                (None, {
                    'fields': [
                        'tilecache_enabled',
                        'tilecache_url',
                        ('tilecache_bbox', 'get_bbox_from_project'),
                        'tilecache_minzoom_level',
                        'tilecache_maxzoom_level',
                        'tilecache_clear_cache',
                    ],
                    'classes': ('tab-tilecache',),
                })
            )
        else:
            fieldsets.append(
                (None, {
                    'fields': [
                        'tilecache_enabled',
                        ('tilecache_bbox', 'get_bbox_from_project'),
                        'tilecache_minzoom_level',
                        'tilecache_maxzoom_level'
                    ],
                    'classes': ('tab-tilecache',),
                })
            )

        fieldsets.append(
            (_('Tile cache config'), {
                'fields': [
                    'tilecache_minZoom_level_chached',
                    'tilecache_maxZoom_level_chached',
                    'tilecache_expiration_time',
                ],
                'classes': ('tab-tilecache',),
            })
        )
        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request)
        return list(readonly_fields) + ['tilecache_url']

    def save_model(self, request, obj, form, change):
        pk = obj.pk
        super().save_model(request, obj, form, change)

        if pk:
            if form.cleaned_data.get('get_bbox_from_project', False):
                bbox = get_service_wms_bbox(obj.service_internal_url)
                if bbox:
                    obj.tilecache_bbox = ','.join(map(str, bbox))
                    obj.save()

            cache_clear_cache = form.cleaned_data.get('tilecache_clear_cache', False)
            if cache_clear_cache:
                GiscubeServiceCache(obj).clear_all()

    def tilecache_url(self, obj):
        relative_url = reverse("qgisserver-tilecache", args=(obj.name,))
        relative_url = remove_app_url(relative_url) + "{z}/{x}/{y}.png"
        return url_slash_join(settings.GISCUBE_URL, relative_url)
