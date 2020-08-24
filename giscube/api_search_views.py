from django.db.models import Q

from geoportal import CATALOG_MODELS
from giscube_search.model_utils import DocumentIndexEditor
from giscube_search.views import GeomSearchView


class FilterByUserMixin:
    def filter_by_user(self, request, qs):
        filter_anonymous = Q(search_data__permissions__user____icontains='v')
        if request.user.is_anonymous:
            qs = qs.filter(filter_anonymous)
        else:
            filter_authenticated_user = Q(search_data__permissions__authenticated_user__icontains='v')
            filter_groups = Q()
            for g in request.user.groups.values_list('name', flat=True):
                cond = {('search_data__permissions__group__%s__icontains' % g): 'v'}
                filter_groups |= Q(**cond)
            filter_user = Q(**{('search_data__permissions__user__%s__icontains' % request.user.username): 'v'})
            qs = qs.filter(filter_anonymous | filter_authenticated_user | filter_user | filter_groups).distinct()
        return qs

    def apply_all_filters(self, request, qs):
        qs = super().apply_all_filters(request, qs)
        qs = self.filter_by_user(request, qs)
        return qs


class GiscubeSearchView(FilterByUserMixin, GeomSearchView):
    permission_classes = []

    def get_model(self):
        return DocumentIndexEditor(name='geoportal').get_model()

    def filter_by_content_type(self, request, qs):
        e = request.GET.get('e', None)
        if e:
            content_types = list(filter(None, e.split(',')))
            if set(content_types).intersection(CATALOG_MODELS) == set(content_types):
                qs = qs.filter(content_type__in=content_types)
            else:
                qs = self.get_model().objects.none()
        else:
            qs = qs.filter(content_type__in=CATALOG_MODELS)
        return qs

    def year_to_first_day(self, d):
        if len(d) == 4:
            d = '%s-01-01' % d
        return d

    def year_to_last_day(self, d):
        if len(d) == 4:
            d = '%s-12-31' % d
        return d

    def filter_by_date(self, request, qs):
        q = request.GET.get('d', None)
        if q:
            dates = q.split(',')
            if len(dates) == 2:
                start = self.year_to_first_day(dates[0])
                end = self.year_to_last_day(dates[1])
                qs = qs.filter(search_data__date__range=(start, end))
            if len(dates) == 1:
                if len(dates[0]) == 4:
                    start = self.year_to_first_day(dates[0])
                    end = self.year_to_last_day(dates[0])
                    qs = qs.filter(search_data__date__range=(start, end))
                else:
                    qs = qs.filter(search_data__date=dates[0])
        return qs

    def apply_all_filters(self, request, qs):
        qs = super().apply_all_filters(request, qs)
        qs = self.filter_by_date(request, qs)
        return qs
