from django.conf.urls import url

from .views import GeoJSONLayerView

urlpatterns = [
    url(r'^geojsonlayers/(?P<layer_name>[^/]+)(.*)',
        GeoJSONLayerView, name='geojsonlayer'),
]
