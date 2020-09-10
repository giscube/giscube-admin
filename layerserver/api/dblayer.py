import logging

from django.db.models import Q
from django.http import HttpResponseServerError

from rest_framework import viewsets
from rest_framework.decorators import action

from ..mapserver import SUPORTED_SHAPE_TYPES, MapserverLayer
from ..models import DataBaseLayer
from ..serializers import DBLayerDetailSerializer, DBLayerSerializer


logger = logging.getLogger(__name__)


class DBLayerViewSet(viewsets.ModelViewSet):
    lookup_field = 'name'
    permission_classes = ()
    queryset = []
    model = DataBaseLayer
    serializer_class = DBLayerSerializer
    user = None

    def get_queryset(self, *args, **kwargs):
        qs = self.model.objects.filter(active=True)
        filter_anonymous = Q(anonymous_view=True) | Q(anonymous_add=True) | Q(anonymous_update=True) \
            | Q(anonymous_delete=True)

        if self.request.user.is_anonymous:
            qs = qs.filter(filter_anonymous)
        else:
            self.user_groups = self.request.user.groups.values_list('name', flat=True)
            filter_group = Q(group_permissions__group__name__in=self.user_groups) & Q(
                Q(group_permissions__can_view=True) | Q(group_permissions__can_add=True) | Q(
                    group_permissions__can_update=True) | Q(group_permissions__can_delete=True))
            filter_user = Q(user_permissions__user=self.request.user) & Q(
                Q(user_permissions__can_view=True) | Q(user_permissions__can_add=True) | Q(
                    user_permissions__can_update=True) | Q(user_permissions__can_delete=True))
            qs = qs.filter(Q(filter_anonymous) | Q(filter_user) | Q(filter_group)).distinct()

        return qs


class DBLayerDetailViewSet(DBLayerViewSet):
    serializer_class = DBLayerDetailSerializer

    def shapetype_not_suported(self, shapetype):
        return HttpResponseServerError('shapetype [%s] not suported' % shapetype)

    @action(methods=['get'], detail=True)
    def wms(self, request, name):
        layer = self.get_object()
        if layer.shapetype not in SUPORTED_SHAPE_TYPES:
            return self.shapetype_not_suported(layer.shapetype)
        ms = MapserverLayer(layer)
        return ms.wms(request)
