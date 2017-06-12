import datetime
import json
import os
from haystack import indexes
from django.conf import settings
from django.utils.translation import ugettext as _
from qgisserver.models import Service


class ServiceIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr='name')
    title = indexes.CharField(model_attr='title')
    has_children = indexes.BooleanField()
    children = indexes.CharField()

    def get_model(self):
        return Service

    def prepare_has_children(self, obj):
        return True

    def prepare_children(self, obj):
        children = []
        url = '%s/qgisserver/services/%s/' % (settings.GISCUBE_URL, obj.name)

        project_file = os.path.basename(obj.project.url)
        filename, file_extension = os.path.splitext(project_file)

        children.append({
            'title': _('View on map'),
            'group': False,
            'type': 'WMS',
            'url': url,
            'layers': filename,
            'projection': '3857',
        })

        return json.dumps(children)

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(active=True)
