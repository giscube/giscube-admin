from giscube.celery import app


@app.task()
def async_geojsonlayer_refresh(pk, force_refresh_data_file):
    from layerserver.utils import geojsonlayer_refresh
    geojsonlayer_refresh(pk, force_refresh_data_file)
