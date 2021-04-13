import mimetypes
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import FileResponse, Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.utils.cache import patch_response_headers
from django.utils.encoding import force_str
from django.views.decorators.cache import never_cache
from django.views.static import serve

from rest_framework.views import APIView

from geoportal.views import GeoportalMixin
from giscube.api_search_views import FilterByUserMixin

from .models import UserAsset


def media_user_asset(request, user_id, filename):
    if request.user:
        user = get_object_or_404(get_user_model(), pk=user_id)
        if request.user == user:
            path = 'user/assets/%s/%s' % (user_id, filename)
            asset = get_object_or_404(UserAsset, user_id=user_id, file=path)
            full_path = asset.file.path
            fd = open(full_path, 'rb')
            file_mime = mimetypes.guess_type(asset.file.name.split('/')[-1])
            response = FileResponse(fd, content_type=file_mime)
            patch_response_headers(response, cache_timeout=60 * 60 * 24 * 7)
            return response

    raise Http404


def private_serve(request, path):
    document_root = settings.MEDIA_ROOT
    show_indexes = False
    if request.user and request.user.is_superuser:
        return serve(request, path, document_root, show_indexes)
    return HttpResponseForbidden()


def web_map_view(request, extra_context):
    """
    Context requires:
    layer_url
    layer_type: tile | wms
    bbox
    base_layer as LEAFLET_CONFIG.TILES
    title
    """

    context = {
        'LEAFLET_CONFIG': {'TILES': 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'}
    }
    context.update(extra_context)
    return render(request, 'admin/giscube/web_map.html', context)


class ResourceFileServer(GeoportalMixin, FilterByUserMixin, APIView):

    def get(self, request, module, model, pk, file):
        allowed = {
            'giscube': ['dataset'],
            'imageserver': ['service'],
            'qgisserver': ['service'],
            'layerserver': ['databaselayer', 'geojsonlayer'],
        }
        if not(model in allowed.get(module, [])):
            return HttpResponseForbidden()

        qs = self.get_model().objects
        qs = qs.filter(content_type='%s.%s' % (module, model), object_id=force_str(pk))
        qs = self.filter_by_user(request, qs)
        if not qs.exists():
            return HttpResponseForbidden()

        document_root = settings.MEDIA_ROOT
        show_indexes = False
        path = os.path.join(module, model, force_str(pk), 'resource', file)
        return serve(request, path, document_root, show_indexes)


@never_cache
def is_authenticated(request):
    success = request.user.is_authenticated
    if success:
        return HttpResponse('true')
    else:
        return HttpResponseForbidden()
