import datetime
import json
import os

from traceback import format_exc

import pytz
import requests

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from django.utils.translation import gettext as _

from django_celery_results.models import TaskResult

from giscube.utils import env_string_parse


GENERATE_GEOJSON_LAYER = 'GENERATE_GEOJSON_LAYER'
GET_DATA_FROM_CACHE = 'GET_DATA_FROM_CACHE'
QUEUE_GENERATE_GEOJSON_LAYER = 'QUEUE_GENERATE_GEOJSON_LAYER'
GENERATE_GEOJSON_LAYER_PENDING = 'GENERATE_GEOJSON_LAYER_PENDING'

GEOJSONLAYER_ERROR_EMPTY = _('Response is empty')
GEOJSONLAYER_ERROR_PARSING_REMOTE_DATA = _('Error parsing remote data')
GEOJSONLAYER_ERROR_PERMISSION = _('Permission problem')
GEOJSONLAYER_ERROR_UNKNOWN = _('Unknown problem, please check GeoJsonLayer configuration (url, headers)')
GEOJSONLAYER_ERROR_REMOTE_SERVER = _('Remote Server problem')
GEOJSONLAYER_ERROR_SAVING = _('Error generating file')
GEOJSONLAYER_ERROR_URL = _('URL problem')


def _get_layer_time(layer, cache_time):
    return (layer.generated_on.astimezone(pytz.utc) + datetime.timedelta(seconds=cache_time)).replace(tzinfo=None)


def geojsonlayer_check_cache(layer):
    """
    Check if the layer has url and has been ever generated.
    Check layer cache_time.
    Check if there is an async_geojsonlayer_refresh pending or in process.
    """
    if layer.url is not None and layer.generated_on is not None:
        cache_time = layer.cache_time or 0
        now = datetime.datetime.utcnow().replace(tzinfo=None)

        if now < _get_layer_time(layer, cache_time):
            return GET_DATA_FROM_CACHE
        else:
            if layer.max_outdated_time is not None:
                if now > _get_layer_time(layer, cache_time + layer.max_outdated_time):
                    geojsonlayer_refresh_layer(layer, force_refresh_data_file=True, generate_popup=False)
                    return GENERATE_GEOJSON_LAYER

        qs = TaskResult.objects.filter(
            task_name='layerserver.tasks.async_geojsonlayer_refresh',
            status__in=['PENDING', 'RECEIVED', 'STARTED'],
            task_args__startswith='(%s,' % layer.pk
        )
        if qs.count() > 0:
            return GENERATE_GEOJSON_LAYER_PENDING

        from .tasks import async_geojsonlayer_refresh
        async_geojsonlayer_refresh.delay(layer.pk, True)
        return QUEUE_GENERATE_GEOJSON_LAYER


def geojsonlayer_refresh(pk, force_refresh_data_file, generate_popup):
    from .models import GeoJsonLayer
    layer = GeoJsonLayer.objects.get(pk=pk)
    return geojsonlayer_refresh_layer(layer, force_refresh_data_file, generate_popup)


def geojsonlayer_remote_data(url, headers):
    result = {}
    try:
        r = requests.get(url, headers=headers)
    except Exception:
        result['status'] = False
        result['error'] = GEOJSONLAYER_ERROR_UNKNOWN
    else:
        if r.status_code >= 200 and r.status_code < 300:
            if r.content:
                result['status'] = True
                result['data'] = r.content.decode(r.encoding or 'utf-8')
            else:
                result['status'] = False
                result['error'] = GEOJSONLAYER_ERROR_EMPTY
        else:
            if r.status_code >= 300 and r.status_code < 400:
                result['status'] = False
                result['error'] = GEOJSONLAYER_ERROR_URL
            elif r.status_code in (401, 403):
                result['status'] = False
                result['error'] = GEOJSONLAYER_ERROR_PERMISSION
            else:
                result['status'] = False
                result['error'] = GEOJSONLAYER_ERROR_REMOTE_SERVER
    return result


def geojsonlayer_get_fields(data):
    fields = []
    try:
        if 'Features' in data and len(data['Features']) > 0:
            fields = list(data['Features'][0]['Properties'].keys())
        if 'features' in data and len(data['features']) > 0:
            fields = list(data['features'][0]['properties'].keys())
    except Exception:
        pass
    return fields


def geojsonlayer_refresh_layer(layer, force_refresh_data_file, generate_popup):
    result = {}
    raw_data = None
    if layer.url:
        remote_file = os.path.join(settings.MEDIA_ROOT, layer.service_path, 'remote.json')
        if force_refresh_data_file or not os.path.isfile(remote_file):
            headers = env_string_parse(layer.headers) if layer.headers else {}
            result = geojsonlayer_remote_data(layer.url, headers)
            if result['status']:
                raw_data = result['data']
                del result['data']
                if os.path.exists(remote_file):
                    os.remove(remote_file)
                layer.data_file.save('remote.json', ContentFile(raw_data), save=True)
                layer.last_fetch_on = timezone.localtime()

    if layer.data_file:
        data = None
        if raw_data:
            try:
                data = json.loads(raw_data)
            except Exception:
                result['status'] = False
                result['error'] = GEOJSONLAYER_ERROR_PARSING_REMOTE_DATA

        if data is None:
            path = os.path.join(settings.MEDIA_ROOT, layer.data_file.path)
            with open(path) as content:
                data = json.load(content)

        layer.fields = ','.join(geojsonlayer_get_fields(data))

        try:
            data['metadata'] = layer.geojson_metadata
            outfile_path = layer.get_data_file_path()
            with open(outfile_path, 'w') as fixed_file:
                fixed_file.write(json.dumps(data, cls=DjangoJSONEncoder))
            if generate_popup:
                layer.popup = layer.get_default_popup()
            layer.generated_on = timezone.localtime()
            layer.save()
            if 'status' not in result:
                result['status'] = True
        except Exception:
            result['status'] = False
            result['error'] = GEOJSONLAYER_ERROR_SAVING
            result['error_exception'] = format_exc()
    return result


def get_list_fields(instance, fields, sort=True):
    list_fields = list(fields.keys())
    if sort:
        list_fields.sort()
    try:
        list_fields.remove(instance.geom_field)
    except Exception:
        pass
    return ','.join(list_fields)
