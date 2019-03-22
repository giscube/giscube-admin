from django.urls import path

from geoportal import views

urlpatterns = [
    path('', views.GeoportalHomeView.as_view(), name='home'),
    path('search/', views.GeoportalSearchView.as_view(), name='search'),
    path('catalog/', views.GeoportalCatalogView.as_view(), name='catalog'),
]
