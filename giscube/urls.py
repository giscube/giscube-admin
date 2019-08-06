from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path

import oauth2_provider.views as oauth2_views
from rest_framework import routers

from giscube import api
from giscube.admin_views import RebuildIndexView

from . import views


router = routers.DefaultRouter()
router.register(r'giscube/category', api.CategoryViewSet, base_name='giscube_category')

router.register(r'giscube/user-assets', api.UserAssetViewSet, base_name='user_assets')

# OAuth2 provider endpoints
oauth2_endpoint_views = [
    path('authorize/', oauth2_views.AuthorizationView.as_view(), name="authorize"),
    path('token/', oauth2_views.TokenView.as_view(), name="token"),
    path('revoke-token/', oauth2_views.RevokeTokenView.as_view(), name="revoke-token"),
]

urlpatterns = [
    # oauth-toolkit
    # auth urls only
    path('o/', include((oauth2_endpoint_views, 'oauth2_provider'), namespace='oauth2_provider')),
    # Examples:
    # url(r'^$', 'giscube.views.home', name='home'),
    # url(r'^$', RedirectView.as_view(url='admin'), name='go-to-admin'),
    path('api/v2/giscube/', include('giscube.api_urls_v2')),
    re_path(r'^media/user/assets/(?P<user_id>\d+)/(?P<filename>.*)$', views.media_user_asset),
    path('admin/admin/', include('app_admin.urls')),
    path('admin/giscube/rebuild_index/', admin.site.admin_view(RebuildIndexView.as_view()), name='rebuild_index'),
    path('admin/', admin.site.urls),
    path('admin/', include('loginas.urls')),
    re_path(r'^media/(?P<path>.*)$', views.private_serve, {'document_root': settings.MEDIA_ROOT}),
]

# Additional modules

if not settings.GISCUBE_IMAGE_SERVER_DISABLED:
    urlpatterns += [
        path('imageserver/', include('imageserver.urls'))
    ]

if not settings.GISCUBE_GIS_SERVER_DISABLED:
    from qgisserver import api as qgisserver_api
    urlpatterns += [
        path('qgisserver/', include('qgisserver.urls'))
    ]
    router.register(r'qgisserver/project', qgisserver_api.ProjectViewSet, basename='qgisserver_project')
    router.register(r'qgisserver/service', qgisserver_api.ServiceViewSet, basename='qgisserver_service')

if not settings.GISCUBE_GEOPORTAL_DISABLED:
    urlpatterns += [
        path('geoportal/', include('geoportal.urls'))
    ]

if not settings.GISCUBE_LAYERSERVER_DISABLED:
    urlpatterns += [
        path('layerserver/', include('layerserver.urls')),
        path('admin/api/v1/layerserver/', include('layerserver.admin_api_urls'))
    ]

# try:
#     import tilescache
#     if tilescache.giscube:
#         urlpatterns += [
#             url(r'^tilescache/', include('tilescache.urls'))
#         ]

urlpatterns += [
    path('api/v1/', include(router.urls)),
]


if settings.USE_CAS:
    import django_cas_ng.views
    cas_login_urls = [
        path('accounts/login', django_cas_ng.views.LoginView.as_view(), name='cas_ng_login'),
        path('accounts/logout', django_cas_ng.views.LogoutView.as_view(), name='cas_ng_logout'),
    ]
    urlpatterns.extend(cas_login_urls)
