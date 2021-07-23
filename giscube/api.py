from django.db.models.functions import Concat

from rest_framework import mixins, parsers, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated

from giscube.notifications import notify_deprecated

from .models import Category, MapConfig, UserAsset
from .serializers import CategorySerializer, MapConfigSerializer, UserAssetSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = []
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

    def dispatch(self, request, *args, **kwargs):
        notify_deprecated('giscube.api.CategoryViewSet', request)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = Category.objects.all()

        # Sort categories setting parents first
        qs = qs.annotate(custom_order=Concat('parent__name', 'name'))
        qs = qs.order_by('custom_order')

        return qs


class UserAssetViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin,
                       mixins.ListModelMixin, viewsets.GenericViewSet):
    lookup_field = 'uuid'
    queryset = []
    parser_classes = (parsers.MultiPartParser,)
    permission_classes = (IsAuthenticated,)
    serializer_class = UserAssetSerializer

    def get_queryset(self):
        queryset = UserAsset.objects.filter(user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MapConfigViewSet(viewsets.ModelViewSet):
    queryset = MapConfig.objects.all()
    serializer_class = MapConfigSerializer
    permission_classes = [AllowAny]
    lookup_field = 'name'
