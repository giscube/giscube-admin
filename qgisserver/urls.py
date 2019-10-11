from django.conf import settings
from django.urls import re_path
from django.views.decorators.csrf import csrf_exempt

from qgisserver.views import QGISProxy


if not settings.GISCUBE_GIS_SERVER_DISABLED:
    urlpatterns = [
        re_path(r'^services/(?P<service_name>[^/]+)(.*)', csrf_exempt(QGISProxy.as_view()), name='qgisserver'),
    ]
