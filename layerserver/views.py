import os

from django.http import (
    HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError,
    FileResponse
)

from .models import GeoJsonLayer


def GeoJSONLayerView(request, layer_name):
    layer_name = ''.join(layer_name.split('.')[:-1])
    layer = GeoJsonLayer.objects.filter(
        active=True,
        name=layer_name).first()
    if not layer or not layer.data_file:
        return HttpResponseNotFound()
    if layer.visibility == 'private' and not request.user.is_authenticated():
        return HttpResponseForbidden()

    path = layer.data_file.path

    if not os.path.isfile(path):
        return HttpResponseServerError(path)

    return FileResponse(open(path, 'rb'))
