from owslib.wms import WebMapService


def get_service_wms_bbox(url):
    wms = WebMapService(url, version='1.1.1')
    layers = list(wms.contents)
    if len(layers) > 0:
        return wms[layers[0]].boundingBoxWGS84
