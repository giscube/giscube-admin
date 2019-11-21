from django.db.models.functions import Concat

from haystack import indexes

from .models import Category


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
