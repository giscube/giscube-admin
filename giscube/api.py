from rest_framework import viewsets, parsers, mixins, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Category, UserAsset
from .serializers import CategorySerializer, UserAssetSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = []
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Category.objects.all().order_by('name')
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
