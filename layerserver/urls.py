# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from .views import (
    GeoJSONLayerView, DBLayerViewSet, DBLayerDetailViewSet,
    DBLayerContentViewSet
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
    'delete': 'delete_multiple'
})

content_detail = DBLayerContentViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

urlpatterns = [
    url(r'^geojsonlayers/(?P<layer_name>[^/]+)(.*)',
        GeoJSONLayerView, name='geojsonlayer'),
    url(r'^databaselayers/(?P<layer_slug>[-\w]+)/data/(?P<pk>[0-9]+)/?$',
        content_detail, name='content-detail'),
    url(r'^databaselayers/(?P<layer_slug>[-\w]+)/data/?$', content_list,
        name='content-list'),
    url(r'^databaselayers/(?P<slug>[-\w]+)(/?)$', layer_detail,
        name='layer-detail'),
    url(r'^databaselayers/$', layer_list, name='layer-list'),
]
