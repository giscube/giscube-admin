from django.contrib.contenttypes.models import ContentType


def resolve_layer(giscube_id):
    if not giscube_id or '.' not in giscube_id:
        return None

    content_type_id, sep, object_id = giscube_id.partition('.')

    try:
        content_type = ContentType.objects.get_for_id(int(content_type_id))
    except (ValueError, ContentType.DoesNotExist):
        return None

    model = content_type.model_class()
    if model is None:
        return None

    try:
        return model.objects.filter(pk=object_id).first()
    except (ValueError, TypeError):
        return None
