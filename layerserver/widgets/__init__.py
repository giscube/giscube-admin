from .auto import AutoWidget
from .base import BaseJSONWidget, BaseWidget
from .choices import ChoicesWidget
from .date import DateWidget
from .datetime import DatetimeWidget
from .image import ImageWidget
from .linkedfield import LinkedfieldWidget
from .relation1n import Relation1NWidget
from .sqlchoices import SqlchoicesWidget


__all__ = ['BaseWidget', 'BaseJSONWidget', 'AutoWidget', 'ChoicesWidget', 'DateWidget', 'DatetimeWidget',
           'ImageWidget', 'LinkedfieldWidget', 'Relation1NWidget', 'SqlchoicesWidget']


widgets_types = {
    'auto': AutoWidget,
    'choices': ChoicesWidget,
    'date': DateWidget,
    'datetime': DatetimeWidget,
    'image': ImageWidget,
    'linkedfield': LinkedfieldWidget,
    'relation1n': Relation1NWidget,
    'sqlchoices': SqlchoicesWidget,
}
