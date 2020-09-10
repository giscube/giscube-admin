import json
import logging
import os

from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponseServerError

from rest_framework import viewsets

from ..models import GeoJsonLayer
from ..serializers import GeoJSONLayerSerializer
from ..utils import geojsonlayer_check_cache


logger = logging.getLogger(__name__)


class GeoJSONLayerViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'name'
    permission_classes = ()
    queryset = []
    model = GeoJsonLayer
    serializer_class = GeoJSONLayerSerializer

    def get_queryset(self, *args, **kwargs):
        qs = self.model.objects.filter(active=True)
        filter_anonymous = Q(anonymous_view=True)

        if self.request.user.is_anonymous:
            qs = qs.filter(filter_anonymous)
        else:
            self.user_groups = self.request.user.groups.values_list('name', flat=True)
            filter_authenticated_user_view = Q(authenticated_user_view=True)
            filter_group = (
                Q(group_permissions__group__name__in=self.user_groups) & Q(group_permissions__can_view=True))
            filter_user = Q(user_permissions__user=self.request.user) & Q(user_permissions__can_view=True)
            qs = qs.filter(
                filter_anonymous | filter_authenticated_user_view | filter_user | filter_group).distinct()

        return qs

    def retrieve(self, request, name):
        layer = self.get_queryset().filter(name=name).first()
        if layer is None:
            raise Http404

        if layer and layer.data_file:
            path = layer.get_data_file_path()
            if os.path.isfile(path):
                geojsonlayer_check_cache(layer)
                return FileResponse(open(path, 'rb'))

        error = {'error': 'DATA_FILE_NOT_FOUND'}
        return HttpResponseServerError(json.dumps(error))
