from django.conf.urls import url

from imageserver import views
from imageserver import admin_views

urlpatterns = [
    url(r'^services/(?P<service_name>[^/]+)/$',
        views.ImageserverProxy.as_view(), name='imageserver'),
    url(r'^raster_optimizer/$',
        admin_views.RasterOptimizerView.as_view(), name='raster_optimizer'),
]
