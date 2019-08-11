import threading

import ujson as json

from haystack.inputs import AutoQuery
from haystack.query import SearchQuerySet
from rest_framework.response import Response
from rest_framework.views import APIView


DEFAULT_SEARCH = [
    {
        'name': 'geoportal',
        'title': 'Geoportal search',
        'url': 'search/',
    },
]

CATALOG_MODELS = ['geoportal.dataset', 'imageserver.service', 'qgisserver.service',
                  'layerserver.geojsonlayer', 'layerserver.databaselayer']

lock = threading.Lock()
thread_local = threading.local()


def get_search_query_set():
    if not hasattr(thread_local, 'search_query_set'):
        # Workaround django-haystack not being thread safe
        lock.acquire()
        thread_local.search_query_set = SearchQuerySet()
        # Evaluate to force setup within locked section
        thread_local.search_query_set.all().count()
        lock.release()

    return thread_local.search_query_set


class ResultsMixin():
    def format_results(self, sqs):
        results = []
        for r in sqs.all():
            try:
                children = json.loads(r.children)
            except Exception as e:
                print(e)
                children = []

            results.append({
                'private': r.private,
                'category_id': r.category_id,
                'title': r.title,
                'description': r.description,
                'keywords': r.keywords,
                'group': getattr(r, 'has_children', False),
                'children': children,
                'options': json.loads(getattr(r, 'options', '{}') or '{}'),
            })
        return Response({'results': results})


class GeoportalCatalogView(ResultsMixin, APIView):
    permission_classes = ()

    def get(self, request):
        category_id = request.GET.get('category_id', '')

        sqs = get_search_query_set().all().filter(django_ct__in=CATALOG_MODELS, category_id__exact=category_id)
        if not request.user.is_authenticated:
            sqs = sqs.exclude(private=True)
        sqs = sqs.order_by('title')
        results = self.format_results(sqs)

        return results


class GeoportalSearchView(ResultsMixin, APIView):
    permission_classes = ()

    def get(self, request):
        q = request.GET.get('q', '')
        sqs = get_search_query_set().all().filter(django_ct__in=CATALOG_MODELS, content=AutoQuery(q))
        if not request.user.is_authenticated:
            sqs = sqs.exclude(private=True)
        results = self.format_results(sqs)

        return results


class GeoportalCategoryView(APIView):
    permission_classes = ()

    def get(self, request):
        sqs = get_search_query_set().all().filter(django_ct='giscube.category').order_by('name')

        results = []
        for r in sqs.all():
            results.append({
                'id': int(r.pk),
                'name': r.name,
                'parent': r.parent,
            })

        return Response(results)
