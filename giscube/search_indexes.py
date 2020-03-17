import json

from django.db.models.functions import Concat

from haystack import indexes

from .models import Category, Dataset
from .utils import get_giscube_id


class CategoryIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    parent = indexes.IntegerField(model_attr='parent__id', null=True)
    name = indexes.CharField(model_attr='name', null=True, default='')
    title = indexes.CharField(model_attr='name', null=True, default='')
    text = indexes.CharField(document=True, use_template=False)

    def get_model(self):
        return Category

    def prepare_title(self, obj):
        return obj.title

    def index_queryset(self, using=None):
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


class DatasetIndex(indexes.SearchIndex, indexes.Indexable):
    giscube_id = indexes.CharField(model_attr='pk')
    text = indexes.CharField(document=True, use_template=True)
    category_id = indexes.IntegerField(model_attr='category_id', null=True)
    category = indexes.CharField(model_attr='category', null=True)
    name = indexes.CharField(model_attr='name')
    title = indexes.CharField(model_attr='title', null=True, default='')
    description = indexes.CharField(model_attr='description', null=True)
    keywords = indexes.CharField(model_attr='keywords', null=True)
    has_children = indexes.BooleanField()
    children = indexes.CharField()
    options = indexes.CharField()
    private = indexes.BooleanField()
    legend = indexes.CharField(model_attr='legend', null=True)

    def get_model(self):
        return Dataset

    def prepare_has_children(self, obj):
        return True

    def prepare_category(self, obj):
        return obj.category.title if hasattr(obj, 'category') and obj.category else None

    def prepare_children(self, obj):
        children = []
        for r in obj.resources.all():
            children.append({
                'title': r.title or r.name,
                'group': False,
                'type': r.type,
                'url': r.url,
                'layers': r.layers,
                'projection': r.projection,
                'giscube': {'getfeatureinfo_support': r.getfeatureinfo_support, 'single_image': r.single_image}
            })
        return json.dumps(children)

    def prepare_giscube_id(self, obj):
        return get_giscube_id(obj)

    def prepare_options(self, obj):
        return obj.options or '{}'

    def prepare_private(self, obj):
        return False

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(active=True)
