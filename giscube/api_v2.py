from url_filter.filtersets import ModelFilterSet

from django.db.models.functions import Concat

from rest_framework import viewsets

from giscube.permissions import FixedDjangoModelPermissions

from .models import Category
from .serializers import CategorySerializer


class CategoryFilter(ModelFilterSet):
    class Meta:
        model = Category
        fiels = '__all__'


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = []
    serializer_class = CategorySerializer
    permission_classes = (FixedDjangoModelPermissions,)

    def get_queryset(self):
        qs = Category.objects.all()
        qs = CategoryFilter(data=self.request.query_params, queryset=qs)
        qs = qs.filter()
        # Sort categories setting parents first
        qs = qs.annotate(custom_order=Concat('parent__name', 'name'))
        qs = qs.order_by('custom_order')
        return qs
