from django.urls import include, path

from rest_framework import routers

from .api_v2 import CategoryViewSet


router = routers.DefaultRouter()
router.register('category', CategoryViewSet, basename='api_v2_giscube_category')

urlpatterns = []

urlpatterns += [
    path('', include(router.urls)),
]
