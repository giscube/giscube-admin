from django.db.models import F, Q

from rest_framework import viewsets, parsers, mixins
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Category, UserAsset
from .serializers import CategorySerializer, UserAssetSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = []
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        # Exclude categories without items
        pks = []
        models = [m.related_model for m in Category._meta.related_objects if not isinstance(m, Category)]
        for m in models:
            pks += m.objects.filter(category__isnull=False).values_list('category__id', flat=True)
        pks = list(set(pks))
        queryset = Category.objects.filter(Q(pk__in=pks) | Q(category__id__in=pks)).order_by('name')
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
