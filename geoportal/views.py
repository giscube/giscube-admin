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
        lock.acquire()
        try:
            sqs = SearchQuerySet().filter(django_ct__in=CATALOG_MODELS, category_id__exact=category_id)
            if not request.user.is_authenticated:
                sqs = sqs.exclude(private=True)
            sqs = sqs.order_by('title')
            results = self.format_results(sqs)
        finally:
            lock.release()

        return results


class GeoportalSearchView(ResultsMixin, APIView):
    permission_classes = ()

    def get(self, request):
        lock.acquire()
        try:
            sqs = SearchQuerySet().filter(django_ct__in=CATALOG_MODELS, content=AutoQuery(request.GET.get('q', '')))
            if not request.user.is_authenticated:
                sqs = sqs.exclude(private=True)
            results = self.format_results(sqs)
        finally:
            lock.release()

        return results


class GeoportalCategoryView(APIView):
    permission_classes = ()

    def get(self, request):
        lock.acquire()
        try:
            sqs = SearchQuerySet().filter(django_ct='giscube.category')
            sqs = sqs.order_by('name')

            results = []
            for r in sqs.all():
                results.append({
                    'id': int(r.pk),
                    'name': r.name,
                    'parent': r.parent,
                })
        finally:
            lock.release()

        return Response(results)
