import datetime
import json
import os
import re

import pytz
import requests

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone

from django_celery_results.models import TaskResult

from .models import GeoJsonLayer


GENERATE_GEOJSON_LAYER = 'GENERATE_GEOJSON_LAYER'
GET_DATA_FROM_CACHE = 'GET_DATA_FROM_CACHE'
QUEUE_GENERATE_GEOJSON_LAYER = 'QUEUE_GENERATE_GEOJSON_LAYER'
GENERATE_GEOJSON_LAYER_PENDING = 'GENERATE_GEOJSON_LAYER_PENDING'


def geojsonlayer_check_cache(layer):
    """
    Check if the layer has url and has been ever generated.
    Check layer cache_time.
    Check if there is an async_geojsonlayer_refresh pending or in process.
    """
    if layer.url is not None and layer.generated_on is not None:
        cache_time = layer.cache_time or 0

        now = datetime.datetime.utcnow().replace(tzinfo=None)
        layer_time = (layer.generated_on.astimezone(pytz.utc) + datetime.timedelta(seconds=cache_time)).replace(
            tzinfo=None)

        if now < layer_time:
            return GET_DATA_FROM_CACHE
        else:
            if layer.max_outdated_time is not None:
                layer_time = (layer.generated_on.astimezone(pytz.utc) + datetime.timedelta(
                    seconds=cache_time + layer.max_outdated_time)).replace(tzinfo=None)
                if now > layer_time:
                    geojsonlayer_refresh_layer(layer, True)
                    return GENERATE_GEOJSON_LAYER

        qs = TaskResult.objects.filter(
            task_name='layerserver.tasks.async_geojsonlayer_refresh',
            status__in=['PENDING', 'RECEIVED', 'STARTED'],
            task_args='(%s,)' % layer.pk
        )
        if qs.count() > 0:
            return GENERATE_GEOJSON_LAYER_PENDING

        from .tasks import async_geojsonlayer_refresh
        async_geojsonlayer_refresh.delay(layer.pk, True)
        return QUEUE_GENERATE_GEOJSON_LAYER


def geojsonlayer_refresh(pk, force_refresh_data_file):
    layer = GeoJsonLayer.objects.get(pk=pk)
    geojsonlayer_refresh_layer(layer, force_refresh_data_file)


def geojsonlayer_refresh_layer(layer, force_refresh_data_file):
    if layer.url:
        headers = {}
        if layer.headers:
            # Extract headers in .env format "key=value"
            matches = re.findall(r'^([^=#\n\r][^=]*)=(.*)$', layer.headers, flags=re.M)
            for k, v in matches:
                headers[k] = v
        remote_file = os.path.join(settings.MEDIA_ROOT, layer.service_path, 'remote.json')
        if force_refresh_data_file or not os.path.isfile(remote_file):
            try:
                r = requests.get(layer.url, headers=headers)
            except Exception:
                raise
            else:
                if r.status_code >= 200 and r.status_code < 300:
                    content = ContentFile(r.text)
                    if content:
                        if os.path.exists(remote_file):
                            os.remove(remote_file)
                        layer.data_file.save('remote.json', content, save=True)
                        layer.last_fetch_on = timezone.localtime()

    if layer.data_file:
        path = os.path.join(settings.MEDIA_ROOT, layer.data_file.path)
        data = json.load(open(path))
        fields = []
        try:
            if 'Features' in data and len(data['Features']) > 0:
                fields = list(data['Features'][0]['Properties'].keys())
            if 'features' in data and len(data['features']) > 0:
                fields = list(data['features'][0]['properties'].keys())
        except Exception:
            pass
        data['metadata'] = layer.metadata
        layer.fields = ','.join(fields)

        outfile_path = layer.get_data_file_path()
        with open(outfile_path, 'w') as fixed_file:
            fixed_file.write(json.dumps(data, cls=DjangoJSONEncoder))
        layer.generated_on = timezone.localtime()
        layer.save()
