import importlib
import re
import random
import string

from django.core.management.commands.inspectdb import Command as InspectdbCommand

models_module = None


def get_klass(field_type):
    global models_module
    if not models_module:
        models_module = importlib.import_module('django.contrib.gis.db.models')
    return getattr(models_module, field_type)


def normalize_col_name(col_name, used_column_names, is_relation):
    return InspectdbCommand.normalize_col_name(InspectdbCommand, col_name, used_column_names, is_relation)


def random_string(string_length=24):
    letters_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_digits) for i in range(string_length))


def table2model(table_name):
    return re.sub(r'[^\w]', '', table_name.title())
