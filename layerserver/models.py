# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from slugify import slugify
import shutil

from django.conf import settings
from django.contrib.gis.db import models
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
# from django.utils.translation import gettext as _

from .mixins import BaseLayerMixin, StyleMixin
from .utils import generateGeoJsonLayer
from giscube.utils import unique_service_directory


def get_jsonlayer_url(instance, filename):
    file_parts = filename.split('.')
    if (file_parts) > 1:
        filename = '%s.%s' % (
            slugify(''.join(file_parts[:-1])), file_parts[-1])
    else:
        filename = slugify(filename)
    return 'layerserver/geojsonlayer/{0}/{1}'.format(instance.id, filename)


class GeoJsonLayer(BaseLayerMixin, StyleMixin, models.Model):
    def upload_path(instance, filename):
        return unique_service_directory(instance, 'remote.json')

    url = models.CharField(max_length=100, null=True, blank=True)
    data_file = models.FileField(upload_to=upload_path,
                                 null=True, blank=True)
    service_path = models.CharField(max_length=255)
    cache_time = models.IntegerField(blank=True, null=True)
    last_fetch_on = models.DateField(null=True, blank=True)
    generated_on = models.DateField(null=True, blank=True)

    @property
    def metadata(self):
        return {
            'description': {
                'title': self.title or '',
                'description': self.description or '',
                'keywords': self.keywords or ''
            },
            'style': {
                'shapetype': self.shapetype,
                'shape_radius': str(self.shape_radius),
                'stroke_color': self.stroke_color,
                'stroke_width': str(self.stroke_width),
                'stroke_dash_array': self.stroke_dash_array,
                'fill_color': self.fill_color,
                'fill_opacity': str(self.fill_opacity)
            }
        }

    def save(self, *args, **kwargs):
        self.name = slugify(self.name)
        super(self.__class__, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.__str__()

    def __str__(self):
        return self.name or self.title

    class Meta:
        """Meta information."""
        verbose_name = 'GeoJSONLayer'
        verbose_name_plural = 'GeoJSONLayers'


@receiver(pre_save, sender=GeoJsonLayer)
def geojsonlayer_pre_save(sender, instance, *args, **kwargs):
    if not hasattr(instance, '_disable_pre_save'):
        instance._disable_pre_save = True
        instance._old_data_file = None
        if instance.pk:
            me = GeoJsonLayer.objects.filter(pk=instance.pk).first()
            instance._old_data = model_to_dict(me)


@receiver(post_save, sender=GeoJsonLayer)
def geojsonlayer_post_save(sender, instance, created, **kwargs):
    if not hasattr(instance, '_disable_post_save'):
        instance._disable_post_save = True
        generateGeoJsonLayer(instance)


@receiver(post_delete, sender=GeoJsonLayer)
def geojsonlayer_delete(sender, instance, **kwargs):
    if instance.service_path:
        path = os.path.join(settings.MEDIA_ROOT, instance.service_path)
        if os.path.exists(path):
            shutil.rmtree(path)
