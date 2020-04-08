import importlib

from django.core.management.base import BaseCommand

from giscube_search.backend import PostgresSearchIndex
from giscube_search.utils import giscube_search_get_app_modules


class Command(BaseCommand):
    def handle(self, *args, **options):
        for app_mod in giscube_search_get_app_modules():
            m = "%s.giscube_search_indexes" % app_mod.__name__
            try:
                search_index_module = importlib.import_module(m)
            except ImportError:
                pass
                continue
            for search_item in getattr(search_index_module, 'index_config', []):
                index = PostgresSearchIndex(config=search_item)
                index.add_items()
