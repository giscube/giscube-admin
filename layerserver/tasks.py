from giscube.celery import app

from celery_progress.backend import ProgressRecorder


@app.task(bind=True)
def async_geojsonlayer_refresh(self, pk, force_refresh_data_file, generate_popup=False, layer_name=None):
    from layerserver.utils import geojsonlayer_refresh
    progress_recorder = ProgressRecorder(self)
    progress_recorder.set_progress(0, 1)
    response = geojsonlayer_refresh(pk, force_refresh_data_file, generate_popup)
    progress_recorder.set_progress(1, 1)
    return response


@app.task(bind=True)
def async_generate_mapfile(self, pk, layer_name=None):
    from layerserver.mapserver import MapserverLayer
    from layerserver.models import DataBaseLayer
    progress_recorder = ProgressRecorder(self)
    progress_recorder.set_progress(0, 1)
    layer = DataBaseLayer.objects.get(pk=pk)
    ms = MapserverLayer(layer)
    ms.write()
    progress_recorder.set_progress(1, 1)
