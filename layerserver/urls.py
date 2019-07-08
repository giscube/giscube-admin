from django.urls import path, re_path

from .api import (DBLayerContentBulkViewSet, DBLayerContentViewSet, DBLayerDetailViewSet, DBLayerViewSet,
                  GeoJSONLayerViewSet)


geojsonlayer_list = GeoJSONLayerViewSet.as_view({
    'get': 'list',
})

geojsonlayer_detail = GeoJSONLayerViewSet.as_view({
    'get': 'retrieve',
})

layer_list = DBLayerViewSet.as_view({
    'get': 'list',
})

layer_detail = DBLayerDetailViewSet.as_view({
    'get': 'retrieve'
})

content_wms = DBLayerDetailViewSet.as_view({
    'get': 'wms'
})

layer_sld = DBLayerDetailViewSet.as_view({
    'get': 'sld'
})

content_list = DBLayerContentViewSet.as_view({
    'get': 'list',
    'post': 'create',
    # 'delete': 'delete_multiple'
})

content_detail = DBLayerContentViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

content_bulk = DBLayerContentBulkViewSet.as_view()

urlpatterns = [
    path('geojsonlayers/', geojsonlayer_list, name='geojsonlayer'),
    re_path(r'^geojsonlayers/(?P<name>[-\w]{1,255})?(\.json|\.geojson)?$',
            geojsonlayer_detail, name='geojsonlayer'),
    path('databaselayers/<slug:name>/data/<str:pk>/<str:attribute>/thumbnail/<path:path>',
         DBLayerContentViewSet.as_view({'get': 'thumbnail_value'}), name='content-detail-thumbnail-value'),
    path('databaselayers/<slug:name>/data/<str:pk>/<str:attribute>/<path:path>',
         DBLayerContentViewSet.as_view({'get': 'file_value'}), name='content-detail-file-value'),
    path('databaselayers/<slug:name>/data/<str:pk>/', content_detail, name='content-detail'),
    path('databaselayers/<slug:name>/data/', content_list, name='content-list'),
    path('databaselayers/<slug:name>/bulk/', content_bulk, name='content-bulk'),
    path('databaselayers/<slug:name>/wms/', content_wms, name='content-wms'),
    path('databaselayers/<slug:name>/sld/', layer_sld, name='layer-sld'),
    path('databaselayers/<slug:name>/', layer_detail, name='layer-detail'),
    path('databaselayers/', layer_list, name='layer-list'),
]
