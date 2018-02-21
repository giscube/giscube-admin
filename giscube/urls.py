from django.conf import settings

from django.conf.urls import include, url
from django.contrib import admin

# from django.views.generic.base import RedirectView

urlpatterns = [
    # Examples:
    # url(r'^$', 'giscube.views.home', name='home'),
    # url(r'^$', RedirectView.as_view(url='admin'), name='go-to-admin'),

    url(r'^admin/', include(admin.site.urls)),
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
