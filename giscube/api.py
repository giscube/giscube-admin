from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Category
from .serializers import CategorySerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = []
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Category.objects.all().order_by('name')
        return queryset
