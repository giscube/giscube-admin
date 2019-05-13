from .auto import AutoWidget
from .base import BaseJSONWidget, BaseWidget
from .choices import ChoicesWidget
from .date import DateWidget
from .image import ImageWidget
from .linkedfield import LinkedfieldWidget
from .sqlchoices import SqlchoicesWidget


__all__ = ['BaseWidget', 'BaseJSONWidget', 'AutoWidget', 'ChoicesWidget', 'DateWidget', 'ImageWidget',
           'LinkedfieldWidget', 'SqlchoicesWidget']


widgets_types = {
    'auto': AutoWidget,
    'choices': ChoicesWidget,
    'date': DateWidget,
    'image': ImageWidget,
    'linkedfield': LinkedfieldWidget,
    'sqlchoices': SqlchoicesWidget,
}
