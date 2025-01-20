import datetime
import ujson as json

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.urls import reverse

from .url import url_slash_join


_content_types = {}


def get_giscube_id(item):
    global _content_types

    model = '%s.%s' % (item._meta.app_label, item._meta.model_name)
    content_type_id = _content_types.get(model)
    if not content_type_id:
        ContentType = apps.get_model('contenttypes', 'ContentType')
        content_type = ContentType.objects.filter(app_label=item._meta.app_label, model=item._meta.model_name).first()
        content_type_id = content_type.id if content_type else None
        _content_types[model] = content_type_id

    if content_type_id:
        return '%s.%s' % (content_type_id, item.pk)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def fix_data_value(value):
    if value:
        if isinstance(value, (datetime.datetime, datetime.date)):
            value = value.isoformat()
    return value


def get_value(obj, field):
    attrs = field.split('.')
    value = obj
    for attr in attrs:
        if value:
            try:
                value = getattr(value, attr)
            except ObjectDoesNotExist:
                value = None
                break
            else:
                value = fix_data_value(value)
        else:
            break
    return value


def prepare_output_data(obj, data={}):
    data['giscube_id'] = get_giscube_id(obj)
    data['private'] = not obj.anonymous_view
    data['category_id'] = obj.category.pk if obj.category else None

    data['description'] = obj.description
    data['keywords'] = obj.keywords
    data['group'] = True
    data['has_children'] = True

    data['legend'] = getattr(obj, 'legend', None)
    data['visible_on_geoportal'] = getattr(obj, 'visible_on_geoportal', False)
    data['options'] = json.loads(getattr(obj, 'options', '{}') or '{}')

    data['filtered_fields'] = [item.strip() for item in obj.filtered_fields.split(',')] if hasattr(obj, 'filtered_fields') and obj.filtered_fields else None
    if hasattr(obj, "get_filters"):
        data['filters'] = obj.get_filters()
    metadata_data = [
        'date', 'language', 'category.name', 'information', 'provider_name', 'provider_web', 'provider_email',
        'summary', 'bbox'
    ]
    metadata_data_keys = [
        'date', 'language', 'category', 'information', 'provider_name', 'provider_web', 'provider_email',
        'summary', 'bbox'
    ]
    metadata = {}
    for k, x in zip(metadata_data_keys, metadata_data):
        metadata[k] = get_value(obj, 'metadata.%s' % x)
    data['metadata'] = metadata
    return data


def prepare_children(obj):
    children = []
    service = {
        'title': obj.title or obj.name,
        'description': obj.description,
        'group': False,
        'choose_individual_layers': obj.choose_individual_layers if hasattr(obj, 'choose_individual_layers') else None,
        'layers': obj.layers
    }
    if obj.tilecache_enabled:
        url = '%s{z}/{x}/{y}.png' % reverse('qgisserver-tilecache', args=(obj.name,))
        url = url_slash_join(settings.GISCUBE_URL, url)
        service.update({
            'type': 'TMS',
            'url': url,
        })
        if obj.tilecache_bbox:
            service.update({ 'bbox': obj.tilecache_bbox })
    else:
        url = url_slash_join(settings.GISCUBE_URL, '/qgisserver/services/%s' % obj.name)
        service.update({
            'type': obj.service_type,
            'url': url,
            'layers': obj.default_layer or '',
            'projection': '3857',
            'giscube': {
                'single_image': obj.wms_single_image,
                'getfeatureinfo_support': obj.wms_getfeatureinfo_enabled,
            },
        })
    children.append(service)
    return children
