from django.urls import path

from .views import AppAdminView


urlpatterns = [
    path('', AppAdminView.as_view()),
]
