from django.urls import path

from .views import visor_user_tracking


urlpatterns = [
    path('visor_user_tracking', visor_user_tracking)
]
