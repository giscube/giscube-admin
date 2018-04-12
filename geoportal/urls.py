from django.conf.urls import url

from geoportal import views

urlpatterns = [
    url(r'^$', views.GeoportalHomeView.as_view(), name='home'),
    # url(r'^search/', include('haystack.urls')),
    url(r'^search/', views.GeoportalSearchView.as_view(), name='search'),
    url(r'^catalog/', views.GeoportalCatalogView.as_view(), name='catalog'),
]
