from .model_factory import ModelFactory
from .model_table import get_fields
from .model_table_helpers import get_klass


def create_dblayer_model(layer):
    return ModelFactory(layer).get_model()


__all__ = [
    'ModelFactory', 'create_dblayer_model', 'get_fields', 'get_klass'
]
