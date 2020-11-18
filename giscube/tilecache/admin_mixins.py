from giscube.tilecache.caches import GiscubeServiceCache
from giscube.utils import get_service_wms_bbox


class TileCacheModelAdminMixin:
    def get_fieldsets(self, request, obj=None):
        fieldsets = list(self.fieldsets)
        if obj:
            fieldsets.append(
                (None, {
                    'fields': [
                        'tilecache_enabled',
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
        return fieldsets

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
