from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from qgisserver.views import QGISProxy

urlpatterns = [
    url(r'^services/(?P<service_name>[^/]+)(.*)',
        csrf_exempt(QGISProxy.as_view()), name='qgisserver'),
]
