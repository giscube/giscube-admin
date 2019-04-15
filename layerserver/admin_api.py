from rest_framework import authentication
from rest_framework import permissions
from rest_framework import viewsets

from .api import GeoJSONLayerViewSet, DBLayerViewSet, DBLayerContentViewSet
from .permissions import DataBaseLayerDjangoPermission
from .serializers import DBLayerDetailSerializer


class AdminGeoJSONLayerViewSet(GeoJSONLayerViewSet):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.DjangoModelPermissions,)

    def get_queryset(self, *args, **kwargs):
        qs = self.model.objects.all()
        return qs


class AdminDBLayerViewSet(viewsets.ReadOnlyModelViewSet, DBLayerViewSet):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.DjangoModelPermissions,)

    def get_queryset(self, *args, **kwargs):
        qs = self.model.objects.all()
        return qs


class AdminDBLayerDetailViewSet(AdminDBLayerViewSet):
    serializer_class = DBLayerDetailSerializer


class AdminDBLayerContentViewSet(viewsets.ReadOnlyModelViewSet, DBLayerContentViewSet):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (DataBaseLayerDjangoPermission,)
