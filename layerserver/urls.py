from django.urls import path

from .views import (
    GeoJSONLayerView, DBLayerViewSet, DBLayerDetailViewSet,
    DBLayerContentViewSet, DBLayerContentBulkViewSet
)


layer_list = DBLayerViewSet.as_view({
    'get': 'list',
})
layer_detail = DBLayerDetailViewSet.as_view({
    'get': 'retrieve'
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
    path('geojsonlayers/<str:layer_name>', GeoJSONLayerView, name='geojsonlayer'),
    path('databaselayers/<slug:layer_slug>/data/<str:pk>/', content_detail, name='content-detail'),
    path('databaselayers/<slug:layer_slug>/data/', content_list, name='content-list'),
    path('databaselayers/<slug:layer_slug>/bulk/', content_bulk, name='content-bulk'),
    path('databaselayers/<slug:slug>/', layer_detail, name='layer-detail'),
    path('databaselayers/', layer_list, name='layer-list'),
]
