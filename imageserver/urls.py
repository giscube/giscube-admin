from django.conf import settings
from django.urls import path, re_path
from django.views.decorators.csrf import csrf_exempt

from .admin_views import RasterOptimizerView
from .views import (ImageServerMapViewerView, ImageServerTileCacheTilesView, ImageServerTileCacheView,
                    ImageServerWMSView)


if not settings.GISCUBE_IMAGE_SERVER_DISABLED:
    urlpatterns = [
        path('services/<str:service_name>/map/',
             ImageServerMapViewerView.as_view(), name='imageserver-map-view'),
        path('services/<str:service_name>/tilecache/',
             ImageServerTileCacheView.as_view(), name='imageserver-tilecache'),
        path('services/<str:service_name>/tilecache/<int:z>/<int:x>/<int:y>.<str:image_format>',
             ImageServerTileCacheTilesView.as_view(), name='imageserver-tilecache-tiles'),
        re_path(r'^services/(?P<service_name>[^/]+)(.*)',
                csrf_exempt(ImageServerWMSView.as_view()), name='imageserver'),
        path('raster_optimizer/', RasterOptimizerView.as_view(), name='raster_optimizer'),

    ]
