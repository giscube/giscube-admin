from url_filter.filtersets import ModelFilterSet


class GISModelFilterSet(ModelFilterSet):
    pass


def filterset_factory(model, fields=None):
    meta = type(str('Meta'), (object,), {'model': model, 'fields': fields})
    filterset = type(str('%sModelFilterSet' % model._meta.object_name),
                     (GISModelFilterSet,), {'Meta': meta})
    return filterset
