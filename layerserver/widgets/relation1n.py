import inspect
import json

from django.db.models import Count, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from django.utils.translation import gettext as _

from .base import BaseJSONWidget


class Relation1NWidget(BaseJSONWidget):
    TEMPLATE = inspect.cleandoc("""
    {
        "dblayer": "layername",
        "to_field": "id",
        "dblayer_fk": "parent_id",
        "count": false
    }
    """)
    ERROR_DBLAYER_REQUIRED = _('\'dblayer\' attribute is required')
    ERROR_TO_FIELD_REQUIRED = _('\'to_field\' attribute is required')
    ERROR_DBLAYER_FK_REQUIRED = _('\'dblayer_fk\' attribute is required')
    base_type = 'relation1n'

    @staticmethod
    def is_valid(value):
        try:
            data = json.loads(value)
        except Exception:
            return Relation1NWidget.ERROR_INVALID_JSON

        if 'dblayer' not in data:
            return Relation1NWidget.ERROR_DBLAYER_REQUIRED

        if 'to_field' not in data:
            return Relation1NWidget.ERROR_TO_FIELD_REQUIRED

        if 'dblayer_fk' not in data:
            return Relation1NWidget.ERROR_DBLAYER_FK_REQUIRED

    @staticmethod
    def serialize_widget_options(obj):
        try:
            options = json.loads(obj.widget_options)
        except Exception:
            return {'error': 'ERROR PARSING WIDGET OPTIONS'}

        data = {'widget_options': options}
        return data

    @staticmethod
    def get_queryset(qs, field, request):
        from layerserver.models import DataBaseLayer
        from layerserver.model_legacy import create_dblayer_model
        if field.get('count') is True:
            dblayer = field.config['dblayer']
            related_layer = DataBaseLayer.objects.filter(name=dblayer).first()
            if not related_layer:
                msg = 'Invalid configuration for DataBaseLayerVirtualField: %s.%s. %s doesn\'t exist' % (
                    field.layer.name, field.name, dblayer)
                raise Exception(msg)

            dblayer_fk = field.config['dblayer_fk']
            related_model = create_dblayer_model(related_layer)
            filter = {dblayer_fk: OuterRef(field.config['to_field'])}
            items = related_model.objects.filter(**filter).order_by().values(dblayer_fk)
            count_items = items.annotate(count=Count(dblayer_fk)).values('count')
            qs = qs.annotate(**{field.name: Coalesce(Subquery(count_items), Value(0))})
            return qs

    @staticmethod
    def serialize_value(model_obj, field):
        if field.get('count') is True:
            value = getattr(model_obj, field.name)
            return {'count': value}
