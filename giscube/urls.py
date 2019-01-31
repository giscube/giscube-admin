from django.conf import settings

from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls.static import static

import oauth2_provider.views as oauth2_views
from rest_framework import routers

from giscube import api
from giscube.admin_views import RebuildIndexView
from qgisserver import api as qgisserver_api


router = routers.DefaultRouter()
router.register(r'giscube/category', api.CategoryViewSet,
                base_name='giscube_category')

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
    url(r'^o/', include((oauth2_endpoint_views, 'oauth2_provider'),
                        namespace='oauth2_provider')),
    # Examples:
    # url(r'^$', 'giscube.views.home', name='home'),
    # url(r'^$', RedirectView.as_view(url='admin'), name='go-to-admin'),

    url(r'^admin/giscube/rebuild_index/$',
        admin.site.admin_view(RebuildIndexView.as_view()),
        name='rebuild_index'),
    url(r'^admin/', admin.site.urls),
    url(r'^admin/', include('loginas.urls')),
]

urlpatterns += static('media', document_root=settings.MEDIA_ROOT)

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
    router.register(r'qgisserver/service', qgisserver_api.ServiceViewSet,
                    base_name='qgisserver_service')

if not settings.GISCUBE_GEOPORTAL_DISABLED:
    urlpatterns += [
        url(r'^geoportal/', include('geoportal.urls'))
    ]

if not settings.GISCUBE_LAYERSERVER_DISABLED:
    urlpatterns += [
        url(r'^layerserver/', include('layerserver.urls'))
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


if settings.USE_CAS:
    import django_cas_ng.views
    cas_login_urls = [
        url(r'^accounts/login$', django_cas_ng.views.LoginView.as_view(),
            name='cas_ng_login'),
        url(r'^accounts/logout$', django_cas_ng.views.LogoutView.as_view(),
            name='cas_ng_logout'),
    ]
    urlpatterns.extend(cas_login_urls)
