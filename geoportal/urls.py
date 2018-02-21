from django.conf.urls import url

from geoportal.views import GeoportalHomeView, GeoportalSearchView

urlpatterns = [
    url(r'^$', GeoportalHomeView.as_view(), name='home'),
    # url(r'^search/', include('haystack.urls')),
    url(r'^search/', GeoportalSearchView.as_view(), name='search'),
]
