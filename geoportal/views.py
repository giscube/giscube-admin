import json

from django.conf import settings
from django.views.generic import View, TemplateView
from django.http import HttpResponse

from haystack.query import SearchQuerySet
from haystack.views import SearchView
from haystack.inputs import AutoQuery


DEFAULT_SEARCH = [
    {
        'name': 'geoportal',
        'title': 'Geoportal search',
        'url': 'search/',
    },
]


class GeoportalHomeView(TemplateView):
    template_name = "geoportal/home.html"

    def get_context_data(self, **kwargs):
        context = super(GeoportalHomeView, self).get_context_data(**kwargs)
        context['searches'] = DEFAULT_SEARCH

        if hasattr(settings, 'GISCUBE_GEOPORTAL'):
            custom_search = settings.GISCUBE_GEOPORTAL.get('SEARCHES', None)
            if custom_search:
                context['searches'] = custom_search
        return context


class ResultsMixin():
    def format_results(self, sqs):
        results = []
        for r in sqs.all():
            try:
                children = json.loads(r.children)
            except Exception, e:
                print e
                children = []

            results.append({
                'category_id': r.category_id,
                'title': r.title,
                'description': r.description,
                'keywords': r.keywords,
                'group': getattr(r, 'has_children', False),
                'children': children,
            })
        return HttpResponse(json.dumps({'results': results}),
                            content_type='application/json')


class GeoportalCatalogView(ResultsMixin, View):
    def get(self, request):
        category_id = request.GET.get('category_id', '')
        sqs = SearchQuerySet().filter(category_id__exact=category_id)
        return self.format_results(sqs)


class GeoportalSearchView(ResultsMixin, View):
    def get(self, request):
        sqs = SearchQuerySet().filter(content=AutoQuery(request.GET.get('q', '')))
        return self.format_results(sqs)
