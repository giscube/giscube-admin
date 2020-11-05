from django.conf import settings


from .utils import url_slash_join
from . model_mixins import RESOURCE_TYPE_CHOICES


class ResourcesIndexMixin:
    def prepare_children(self, obj):
        children = []
        for r in obj.resources.all():
            url = r.url
            if r.type == RESOURCE_TYPE_CHOICES.document and r.file is not None:
                url = url_slash_join(settings.SITE_URL, r.file.url)
            children.append({
                'title': r.title or r.name,
                'description': r.description,
                'group': False,
                'type': r.type,
                'url': url,
                'layers': r.layers,
                'projection': r.projection,
                'giscube': {
                    'getfeatureinfo_support': r.getfeatureinfo_support,
                    'single_image': r.single_image,
                    'downloadable': r.downloadable
                }
            })
        return children
