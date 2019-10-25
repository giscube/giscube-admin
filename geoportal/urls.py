from django.urls import path

from geoportal import views


urlpatterns = [
    path('search/', views.GeoportalSearchView.as_view(), name='geoportal-search'),
    path('catalog/', views.GeoportalCatalogView.as_view(), name='geoportal-catalog'),
    path('category/', views.GeoportalCategoryView.as_view(), name='geoportal-category'),
    path('giscube_id/<giscube_ids>', views.GeoportalGiscubeIdView.as_view(), name='geoportal-giscube_id'),
]
