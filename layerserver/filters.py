# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from url_filter.filtersets import ModelFilterSet


def filterset_factory(model, fields=None):
    meta = type(str('Meta'), (object,), {'model': model, 'fields': fields})
    filterset = type(str('%sModelFilterSet' % model._meta.object_name),
                     (ModelFilterSet,), {'Meta': meta})
    return filterset
