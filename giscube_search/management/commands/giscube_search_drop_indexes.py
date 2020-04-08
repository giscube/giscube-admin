import importlib

from django.core.management.base import BaseCommand

from giscube_search.model_utils import DocumentIndexEditor
from giscube_search.utils import giscube_search_get_app_modules


class Command(BaseCommand):
    def handle(self, *args, **options):
        """Drops all index tables"""
        done = []
        for app_mod in giscube_search_get_app_modules():
            try:
                m = "%s.giscube_search_indexes" % app_mod.__name__
                search_index_module = importlib.import_module(m)
            except ImportError:
                pass
                continue

            for search_item in getattr(search_index_module, 'index_config', []):
                index = search_item.get_index()
                if not (index in done):
                    done.append(index)
                    DocumentIndexEditor(name=index).delete()
