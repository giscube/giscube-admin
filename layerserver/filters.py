from url_filter.filters import Filter
from url_filter.filtersets import ModelFilterSet

from django import forms

from .models import DataBaseLayerVirtualField


class GISModelFilterSet(ModelFilterSet):
    pass


def filterset_factory(model, fields, virtual_fields=None):
    filters = {}
    if virtual_fields:
        for name, field in virtual_fields.items():
            if field.widget == DataBaseLayerVirtualField.WIDGET_CHOICES.relation1n and 'count' in field.config \
                    and field.config['count']:
                filters[name] = Filter(form_field=forms.IntegerField())

    meta = type(str('Meta'), (object,), {'model': model, 'fields': fields})
    filterset = type(str('%sModelFilterSet' % model._meta.object_name),
                     (GISModelFilterSet,), {'Meta': meta, **filters})
    return filterset
