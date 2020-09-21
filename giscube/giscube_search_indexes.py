from django.db.models.functions import Concat

from geoportal.indexes_mixin import GeoportalSearchIndexMixin
from giscube_search.base_index import BaseModelIndex
from .giscube_search_indexes_mixins import ResourcesIndexMixin
from .indexes_mixin import PermissionIndexMixin
from .models import Category, Dataset


class DatasetIndex(ResourcesIndexMixin, PermissionIndexMixin, GeoportalSearchIndexMixin):
    pass


class CategoryIndex(BaseModelIndex):
    def get_items(self):
        # Exclude categories without items
        pks = []
        models = [m.related_model for m in self.get_model()._meta.related_objects
                  if m.related_model != self.get_model()]
        for m in models:
            for pk in m.objects.filter(active=True, category__isnull=False).values_list(
                    'category_id', 'category__parent_id'):
                pks.append(pk[0])
                if pk[1] is not None:
                    pks.append(pk[1])
        pks = list(set(pks))
        # Filtered search
        queryset = Category.objects.filter(pk__in=pks).prefetch_related('parent')
        queryset = queryset.annotate(custom_order=Concat('parent__name', 'name'))
        queryset = queryset.order_by('custom_order')

        return queryset


index_config = [
    DatasetIndex({
        'index': 'geoportal',
        'model': Dataset
    }),
    CategoryIndex({
        'index': 'geoportal',
        'model': Category,
        'fields': ['name'],
        'output_data': ['id', 'name', 'color', 'parent.id'],
        'output_data_keys': ['id', 'name', 'color', 'parent'],
        'search_data': ['title']
    })
]
