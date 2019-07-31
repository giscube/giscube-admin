from giscube.celery import app


@app.task()
def async_geojsonlayer_refresh(pk, force_refresh_data_file, generate_popup=False):
    from layerserver.utils import geojsonlayer_refresh
    return geojsonlayer_refresh(pk, force_refresh_data_file, generate_popup)


@app.task()
def async_generate_mapfile(pk):
    from layerserver.models import DataBaseLayer
    from layerserver.mapserver import MapserverLayer
    layer = DataBaseLayer.objects.get(pk=pk)
    ms = MapserverLayer(layer)
    ms.write()
