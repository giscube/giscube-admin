from django.conf import settings

from django.conf.urls import include, url
from django.contrib import admin
# from django.views.generic.base import RedirectView
import oauth2_provider.views as oauth2_views
from rest_framework import routers

from qgisserver import api as qgisserver_api

router = routers.DefaultRouter()

# OAuth2 provider endpoints
oauth2_endpoint_views = [
    url(r'^authorize/$', oauth2_views.AuthorizationView.as_view(),
        name="authorize"),
    url(r'^token/$', oauth2_views.TokenView.as_view(), name="token"),
    url(r'^revoke-token/$', oauth2_views.RevokeTokenView.as_view(),
        name="revoke-token"),
]

urlpatterns = [
    # oauth-toolkit
    # auth urls only
    url(r'^o/', include(oauth2_endpoint_views, namespace="oauth2_provider")),

    # Examples:
    # url(r'^$', 'giscube.views.home', name='home'),
    # url(r'^$', RedirectView.as_view(url='admin'), name='go-to-admin'),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/', include('loginas.urls')),
]

# Additional modules

if not settings.GISCUBE_IMAGE_SERVER_DISABLED:
    urlpatterns += [
        url(r'^imageserver/', include('imageserver.urls'))
    ]

if not settings.GISCUBE_GIS_SERVER_DISABLED:
    urlpatterns += [
        url(r'^qgisserver/', include('qgisserver.urls'))
    ]
    router.register(r'qgisserver/project', qgisserver_api.ProjectViewSet,
                    base_name='qgisserver_project')

if not settings.GISCUBE_GEOPORTAL_DISABLED:
    urlpatterns += [
        url(r'^geoportal/', include('geoportal.urls'))
    ]

# try:
#     import tilescache
#     if tilescache.giscube:
#         urlpatterns += [
#             url(r'^tilescache/', include('tilescache.urls'))
#         ]

urlpatterns += [
    url(r'api/v1/', include(router.urls)),
]
