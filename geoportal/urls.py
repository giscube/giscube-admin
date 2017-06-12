from django.conf.urls import patterns, include, url

from geoportal.views import GeoportalHomeView, GeoportalSearchView

urlpatterns = patterns('',
    url(r'^$', GeoportalHomeView.as_view(), name='home'),
    # url(r'^search/', include('haystack.urls')),
    url(r'^search/', GeoportalSearchView.as_view(), name='search'),
)
