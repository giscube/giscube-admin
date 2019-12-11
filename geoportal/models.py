from django.db import models
from django.utils.translation import gettext as _

from giscube.models import Category
from giscube.validators import validate_options_json_format


class Dataset(models.Model):
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    keywords = models.CharField(max_length=200, null=True, blank=True)
    active = models.BooleanField(default=True, help_text='Enable/disable usage')
    options = models.TextField(_('options'), null=True, blank=True, help_text='json format. Ex: {"maxZoom": 20}',
                               validators=[validate_options_json_format])

    def __str__(self):
        return '%s' % self.title or self.name


RESOURCE_TYPE_CHOICES = [
    ('TMS', 'TMS'),
    ('WMS', 'WMS'),
]


class Resource(models.Model):
    dataset = models.ForeignKey(
        Dataset, related_name='resources', on_delete=models.CASCADE)
    type = models.CharField(max_length=12, choices=RESOURCE_TYPE_CHOICES)
    name = models.CharField(max_length=50)
    title = models.CharField(max_length=100, null=True, blank=True)
    path = models.CharField(max_length=255, null=True, blank=True)
    url = models.CharField(max_length=255, null=True, blank=True)
    layers = models.CharField(max_length=255, null=True, blank=True)
    projection = models.IntegerField(help_text='EPSG code')
    getfeatureinfo_support = models.BooleanField(_('WMS GetFeatureInfo support'), default=True)
    single_image = models.BooleanField(_('Use single image'), default=False)

    def __str__(self):
        return '%s' % self.title or self.name
