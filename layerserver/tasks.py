from giscube.celery import app


@app.task()
def async_geojsonlayer_refresh(pk):
    from layerserver.utils import geojsonlayer_refresh
    geojsonlayer_refresh(pk)
