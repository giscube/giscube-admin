from django.shortcuts import get_object_or_404

from django_celery_results.models import TaskResult
from rest_framework import authentication, viewsets

from giscube.permissions import FixedDjangoModelPermissions

from .api import DBLayerContentViewSet, DBLayerViewSet, GeoJSONLayerViewSet
from .models import GeoJsonLayer
from .permissions import DataBaseLayerDjangoPermission
from .serializers import DBLayerDetailSerializer, GeoJSONLayerLogSerializer


class AdminGeoJSONLayerViewSet(GeoJSONLayerViewSet):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (FixedDjangoModelPermissions,)

    def get_queryset(self, *args, **kwargs):
        qs = self.model.objects.all()
        return qs


class AdminGeoJSONLayerLogViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (FixedDjangoModelPermissions,)
    serializer_class = GeoJSONLayerLogSerializer

    def dispatch(self, request, layer, *args, **kwargs):
        self.layer = get_object_or_404(GeoJsonLayer, name=layer)
        return super().dispatch(request, layer, *args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        qs = TaskResult.objects.filter(
            task_name='layerserver.tasks.async_geojsonlayer_refresh',
            status__in=['PENDING', 'RECEIVED', 'STARTED', 'SUCCESS', 'FAILURE'],
            task_args__startswith='(%s,' % self.layer.pk
        ).order_by('-date_done')[:10]
        return qs


class AdminDBLayerViewSet(viewsets.ReadOnlyModelViewSet, DBLayerViewSet):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (FixedDjangoModelPermissions,)

    def get_queryset(self, *args, **kwargs):
        qs = self.model.objects.all()
        return qs


class AdminDBLayerDetailViewSet(AdminDBLayerViewSet):
    serializer_class = DBLayerDetailSerializer


class AdminDBLayerContentViewSet(viewsets.ReadOnlyModelViewSet, DBLayerContentViewSet):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (DataBaseLayerDjangoPermission,)
