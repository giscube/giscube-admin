from django.urls import include, path

from rest_framework import routers

from incidences.api import IncidenceViewSet

from .api_search_views import GiscubeSearchView
from .api_v2 import CategoryViewSet


router = routers.DefaultRouter()
router.register('category', CategoryViewSet, basename='api_v2_giscube_category')
router.register('incidence', IncidenceViewSet, basename='incidence')


urlpatterns = [
    path('', include(router.urls)),
    path('search/', GiscubeSearchView.as_view(), name='giscube-search'),
]
