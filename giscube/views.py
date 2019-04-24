import mimetypes

from django.contrib.auth import get_user_model
from django.http import FileResponse, Http404, HttpResponseForbidden

from django.shortcuts import get_object_or_404
from django.utils.cache import patch_response_headers
from django.views.static import serve

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


def private_serve(request, path, document_root=None, show_indexes=False):
    if request.user and request.user.is_superuser:
        return serve(request, path, document_root, show_indexes)
    return HttpResponseForbidden()
