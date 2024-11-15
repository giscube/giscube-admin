from django.urls import include, path

from rest_framework import routers

from .api import LayerRegisterViewSet, ToolRegisterViewSet
from .views import visor_user_tracking


router = routers.DefaultRouter()
router.register(r"layer-register", LayerRegisterViewSet, basename="layer-register")
router.register(r"tool-register", ToolRegisterViewSet, basename="tool-register")

urlpatterns = [
    path('visor_user_tracking', visor_user_tracking),
    path("api/v1/", include(router.urls))
]
