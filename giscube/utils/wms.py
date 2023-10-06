from owslib.wms import WebMapService

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.translation import gettext as _


def get_service_wms_bbox(url):
    wms = WebMapService(url, version='1.1.1')
    layers = list(wms.contents)
    if len(layers) > 0:
        return wms[layers[0]].boundingBoxWGS84


def get_wms_layers(wms_url):
    url_validator = URLValidator()
    try:
        url_validator(wms_url)
    except ValidationError:
        raise ValidationError({'url': _('This URL is not valid.')})
    try:
        wms = WebMapService(wms_url)
        return ','.join(list(wms.contents))
    except Exception:
        raise ValidationError({'url': _('This URL is not a valid WMS endpoint.')})
