import datetime
import json
import os
import pytz
import re
import requests

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from django_celery_monitor.models import TaskState

from giscube.json_utils import DateTimeJSONEncoder

from .models import GeoJsonLayer


def geojsonlayer_check_cache(layer):
    """
    Check if the layer has url and has been ever generated.
    Check layer cache_time.
    Check if there is an async_geojsonlayer_refresh pending or in process.
    """
    if layer.url and layer.generated_on:
        cache_time = layer.cache_time or 0
        now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        layer_time = layer.generated_on.utcnow().replace(tzinfo=pytz.utc) + datetime.timedelta(seconds=cache_time)

        if now < layer_time:
            return

        qs = TaskState.objects.filter(
            name='layerserver.tasks.async_geojsonlayer_refresh',
            state__in=['PENDING', 'RECEIVED', 'STARTED'],
            args='(%s,)' % layer.pk
        )
        if qs.count() > 0:
            return

        from .tasks import async_geojsonlayer_refresh
        async_geojsonlayer_refresh.delay(layer.pk)


def geojsonlayer_refresh(pk):
    layer = GeoJsonLayer.objects.get(pk=pk)
    geojsonlayer_refresh_layer(layer)


def geojsonlayer_refresh_layer(layer):
    if layer.url:
        headers = {}
        if layer.headers:
            # Extract headers in .env format "key=value"
            matches = re.findall(r'^([^=#\n\r][^=]*)=(.*)$', layer.headers, flags=re.M)
            for k, v in matches:
                headers[k] = v
        try:
            r = requests.get(layer.url, headers=headers)
        except Exception as e:
            print('Error getting file %s' % e)
        else:
            if r.status_code >= 200 and r.status_code < 300:
                content = ContentFile(r.text)
                if content:
                    remote_file = os.path.join(
                        settings.MEDIA_ROOT, layer.service_path, 'remote.json')
                    if os.path.exists(remote_file):
                        os.remove(remote_file)
                    layer.data_file.save('remote.json', content, save=True)
                    layer.last_fetch_on = timezone.localtime()

    if layer.data_file:
        path = os.path.join(settings.MEDIA_ROOT, layer.data_file.path)
        data = json.load(open(path))
        data['metadata'] = layer.metadata
        outfile_path = layer.get_data_file_path()
        with open(outfile_path, 'wb') as fixed_file:
            fixed_file.write(json.dumps(data))
        layer.generated_on = timezone.localtime()
        layer.save()
