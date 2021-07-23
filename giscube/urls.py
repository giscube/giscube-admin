import os

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path

from oauth2_provider import views as oauth2_views
from django.contrib.auth import views as auth_views
from rest_framework import routers

from giscube import api

from . import views


router = routers.DefaultRouter()
router.register(r'giscube/category', api.CategoryViewSet, basename='giscube_category')

router.register(r'giscube/user-assets', api.UserAssetViewSet, basename='user_assets')

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
    path('', include('giscube_search.urls')),
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('api/v2/giscube/', include('giscube.api_urls_v2')),
    re_path(r'^media/user/assets/(?P<user_id>\d+)/(?P<filename>.*)$', views.media_user_asset),
    path('admin/app_admin/', include('app_admin.urls')),
    path('admin/', admin.site.urls),
    path('admin/', include('loginas.urls')),
    path('media/<str:module>/<str:model>/<int:pk>/resource/<str:file>', views.ResourceFileServer.as_view()),
    re_path(r'^media/(?P<path>.*)$', views.private_serve),
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
        path('geoportal/', include('geoportal.urls')),
    ]
    router.register(r'mapconfig', api.MapConfigViewSet, basename='map_config')

if not settings.GISCUBE_LAYERSERVER_DISABLED:
    urlpatterns += [
        path('layerserver/', include('layerserver.urls')),
        path('admin/api/v1/layerserver/', include('layerserver.admin_api_urls'))
    ]

if not settings.IS_AUTHENTICATED_DISABLED:
    urlpatterns += [
        path('is_authenticated', views.is_authenticated),
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

for plugin in settings.GISCUBE_PLUGINS:
    plugins_url_path = '%s/%s/src/%s/urls.py' % (settings.GISCUBE_PLUGINS_PATH, plugin, plugin)
    if os.path.isfile(plugins_url_path):
        urlpatterns.append(path('plugins/%s/' % plugin, include('%s.urls' % plugin)))
