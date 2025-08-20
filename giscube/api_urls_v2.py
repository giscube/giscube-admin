from django.urls import include, path

from rest_framework import routers

from incidences.api import IncidenceViewSet

from .api_search_views import GiscubeSearchView
from .api_v2 import new_accesslog, CategoryViewSet, list_userslog


router = routers.DefaultRouter()
router.register('category', CategoryViewSet, basename='api_v2_giscube_category')
router.register('incidence', IncidenceViewSet, basename='incidence')


urlpatterns = [
    path('', include(router.urls)),
    path('search/', GiscubeSearchView.as_view(), name='giscube-search'),
    path('new_accesslog/', new_accesslog, name='new_accesslog'),
    path('list_userslog/', list_userslog, name='list_userslog'),
]
