from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse

from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from geoportal.data import PREDEFINED_MAP_TOOLS
from giscube.api_search_views import FilterByUserMixin
from giscube.models import MapTool
from giscube.serializers import MapToolSerializer
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
        return qs


class GeoportalCatalogFilteredByCategoryView(GeoportalCatalogView):
    def apply_all_filters(self, request, qs):
        qs = super().apply_all_filters(request, qs)
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


class GeoportalCategoryCatalogView(GeoportalCategoryView):
    def get(self, request):
        # TODO: Refactor
        v = GeoportalCatalogView()
        rows = v.get_queryset(request)
        content = {}
        for r in rows:
            if r.output_data['category_id']:
                if r.output_data['category_id'] not in content:
                    content[r.output_data['category_id']] = []
                content[r.output_data['category_id']].append(r.output_data)

        raw_data = []
        with_content = []

        for x in self.get_queryset(request):
            category = x.output_data
            if category['id'] in content:
                category['content'] = content[category['id']]
            raw_data.append(category)
            with_content.append(category['id'])
            if category['parent']:
                with_content.append(category['parent'])
        data = [x for x in raw_data if category['id'] in with_content]

        return Response(data)


class GeoportalMapToolsView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        tools = MapTool.objects.filter(visible_on_geoportal=True).order_by('order')
        anonymous = Q(anonymous_view=True)
        if request.user.is_anonymous:
            tools = tools.filter(anonymous)
        else:
            authenticated = (
                Q(authenticated_user_view=True)
                | Q(user_permissions__user=request.user)
                | Q(group_permissions__group__user=request.user)
            )
            tools = tools.filter(anonymous | authenticated)

        serialized = MapToolSerializer(tools, many=True)
        return Response({"tools": serialized.data})


class LoadPredefinedMapTools(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        for order, tool_data in enumerate(PREDEFINED_MAP_TOOLS):
            tool = {
                "order": order + 1,
                "visible_on_geoportal": True,
                "anonymous_view": True,
                "authenticated_user_view": False,
            }
            if not tool_data.get("action_type"):
                tool['action_type'] = 'to'
                tool['to'] = tool_data.get('to', tool_data['name'])
            tool.update(tool_data)
            MapTool.objects.update_or_create(
                name=tool['name'],
                defaults=tool,
            )

        changelist_url = reverse("admin:giscube_maptool_changelist")
        return redirect(changelist_url)
