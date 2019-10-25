from django.apps import apps


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
