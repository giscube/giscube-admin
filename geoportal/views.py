from rest_framework.response import Response

from giscube.api_search_views import FilterByUserMixin
from giscube_search.model_utils import DocumentIndexEditor
from giscube_search.views import SearchView

from . import CATALOG_MODELS


DEFAULT_SEARCH = [
    {
        'name': 'geoportal',
        'title': 'Geoportal search',
        'url': 'search/',
    },
]


class GeoportalMixin(object):
    permission_classes = []

    def get_model(self):
        return DocumentIndexEditor(name='geoportal').get_model()


class CatalogMixin(FilterByUserMixin, GeoportalMixin):
    def filter_by_content_type(self, request, qs):
        qs = qs.filter(content_type__in=CATALOG_MODELS)
        return qs

    def filter_by_visible_on_geoportal(self, request, qs):
        qs = qs.filter(search_data__visible_on_geoportal=True)
        return qs

    def apply_all_filters(self, request, qs):
        qs = super().apply_all_filters(request, qs)
        qs = self.filter_by_visible_on_geoportal(request, qs)
        return qs


class GeoportalCatalogView(CatalogMixin, SearchView):
    def apply_all_filters(self, request, qs):
        qs = super().apply_all_filters(request, qs)
        qs = qs.order_by('output_data__title')
        try:
            category_id = int(request.GET.get('category_id'))
        except Exception:
            qs = qs.none()
        else:
            qs = qs.filter(search_data__category_id=category_id)
        return qs


class GeoportalGiscubeIdView(CatalogMixin, SearchView):
    def filter_by_giscube_ids(self, qs):
        giscube_ids = filter(None, self.giscube_ids.split(','))
        qs = qs.filter(search_data__giscube_id__in=giscube_ids)
        return qs

    def apply_all_filters(self, request, qs):
        qs = super().apply_all_filters(request, qs)
        qs = self.filter_by_giscube_ids(qs)
        return qs

    def get_data(self, request):
        giscube_ids = filter(None, self.giscube_ids.split(','))
        sorted_giscube_ids = {giscube_id: None for giscube_id in [x for x in giscube_ids]}
        for x in self.get_queryset(request):
            sorted_giscube_ids[x.search_data['giscube_id']] = x.output_data
        return list(sorted_giscube_ids.values())

    def get(self, request, giscube_ids):
        self.giscube_ids = giscube_ids
        return super().get(request)


class GeoportalSearchView(CatalogMixin, SearchView):
    def filter_by_q(self, request, qs):
        q = request.GET.get('q', None)
        if q:
            qs = qs.search(q)
        else:
            qs = qs.none()
        return qs


class GeoportalCategoryView(GeoportalMixin, SearchView):
    def filter_by_content_type(self, request, qs):
        qs = qs.filter(content_type='giscube.category')
        return qs

    def apply_all_filters(self, request, qs):
        qs = super().apply_all_filters(request, qs)
        qs = qs.order_by('search_data__title')
        return qs

    def get(self, request):
        data = self.get_data(request)
        return Response(data)
