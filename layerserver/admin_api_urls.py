from django.urls import path, re_path

from .admin_api import (
    AdminDBLayerContentViewSet, AdminDBLayerDetailViewSet, AdminGeoJSONLayerViewSet)

geojsonlayer_detail = AdminGeoJSONLayerViewSet.as_view({
    'get': 'retrieve',
})

layer_detail = AdminDBLayerDetailViewSet.as_view({
    'get': 'retrieve'
})

content_list = AdminDBLayerContentViewSet.as_view({
    'get': 'list'
})


urlpatterns = [
    re_path(r'^geojsonlayers/(?P<name>[-\w]{1,255})?(\.json|\.geojson)?$',
            geojsonlayer_detail, name='admin-api-geojsonlayer-detail'),
    path('databaselayers/<slug:layer_slug>/data/', content_list, name='admin-api-layer-content-list'),
    path('databaselayers/<slug:slug>/', layer_detail, name='admin-api-layer-detail'),
]
