from .auto import AutoWidget
from .base import BaseJSONWidget, BaseWidget
from .choices import ChoicesWidget
from .creationdate import CreationDateWidget
from .creationdatetime import CreationDatetimeWidget
from .creationuser import CreationUserWidget
from .date import DateWidget
from .datetime import DatetimeWidget
from .distinctvalues import DisctintValuesWidget
from .foreignkey import ForeignKeyWidget
from .image import ImageWidget
from .linkedfield import LinkedfieldWidget
from .modificationdate import ModificationDateWidget
from .modificationdatetime import ModificationDatetimeWidget
from .modificationuser import ModificationUserWidget
from .relation1n import Relation1NWidget
from .sqlchoices import SqlchoicesWidget


__all__ = ['BaseWidget', 'BaseJSONWidget', 'AutoWidget', 'ChoicesWidget', 'CreationDateWidget',
           'CreationDatetimeWidget', 'CreationUserWidget', 'DateWidget', 'DatetimeWidget', 'DisctintValuesWidget',
           'ForeignKeyWidget', 'ImageWidget', 'LinkedfieldWidget', 'ModificationDateWidget',
           'ModificationDatetimeWidget', 'ModificationUserWidget', 'Relation1NWidget', 'SqlchoicesWidget'
           ]


widgets_types = {
    'auto': AutoWidget,
    'choices': ChoicesWidget,
    'creationdate': CreationDateWidget,
    'creationdatetime': CreationDatetimeWidget,
    'creationuser': CreationUserWidget,
    'date': DateWidget,
    'datetime': DatetimeWidget,
    'distinctvalues': DisctintValuesWidget,
    'foreignkey': ForeignKeyWidget,
    'image': ImageWidget,
    'linkedfield': LinkedfieldWidget,
    'modificationdate': ModificationDateWidget,
    'modificationdatetime': ModificationDatetimeWidget,
    'modificationuser': ModificationUserWidget,
    'relation1n': Relation1NWidget,
    'sqlchoices': SqlchoicesWidget,
}
