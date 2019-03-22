from django.urls import path, re_path

from imageserver import views
from imageserver import admin_views

urlpatterns = [
    re_path(r'^services/(?P<service_name>[^/]+)/$', views.ImageserverProxy.as_view(), name='imageserver'),
    path('raster_optimizer/', admin_views.RasterOptimizerView.as_view(), name='raster_optimizer'),
]
