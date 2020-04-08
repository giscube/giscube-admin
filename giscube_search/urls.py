from django.contrib import admin
from django.urls import path

from .admin_views import RebuildGiscubeSearchIndexView


urlpatterns = [
    path('admin/giscube_search/rebuild_giscube_search_index/',
         admin.site.admin_view(RebuildGiscubeSearchIndexView.as_view()),
         name='rebuild_giscube_search_index'),
]
