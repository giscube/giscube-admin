from django.db.models import F

from rest_framework import viewsets, parsers, mixins
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Category, UserAsset
from .serializers import CategorySerializer, UserAssetSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = []
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Category.objects.all()
        # Sort categories setting parents first
        queryset = queryset.order_by(F('parent__name').desc(nulls_last=False), 'name')
        return queryset


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
