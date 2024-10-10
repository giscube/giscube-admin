from django.conf import settings
from django.urls import path, re_path
from django.views.decorators.csrf import csrf_exempt

from qgisserver.views import (QGISServerMapViewerView, QGISServerTileCacheTilesView, QGISServerTileCacheView,
                              QGISServerWMSView)


if not settings.GISCUBE_GIS_SERVER_DISABLED:

    urlpatterns = [
        path('services/<str:service_name>/map/',
             QGISServerMapViewerView.as_view(), name='qgisserver-map-view'),
        path('services/<str:service_name>/tilecache/',
             QGISServerTileCacheView.as_view(), name='qgisserver-tilecache'),
        path('services/<str:service_name>/tilecache/<int:z>/<int:x>/<str:y>.<str:image_format>',
             QGISServerTileCacheTilesView.as_view(), name='qgisserver-tilecache-tiles'),
        re_path(r'^services/(?P<service_name>[^/]+)(.*)', csrf_exempt(QGISServerWMSView.as_view()), name='qgisserver'),
    ]
