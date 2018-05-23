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
from django.utils.translation import gettext as _

from .mixins import BaseLayerMixin, StyleMixin
import layerserver.model_legacy as model_legacy
from .utils import generateGeoJsonLayer
from giscube.utils import unique_service_directory
from giscube.models import DBConnection


def get_jsonlayer_url(instance, filename):
    file_parts = filename.split('.')
    if (file_parts) > 1:
        filename = '%s.%s' % (
            slugify(''.join(file_parts[:-1])), file_parts[-1])
    else:
        filename = slugify(filename)
    return 'layerserver/geojsonlayer/{0}/{1}'.format(instance.id, filename)


def geojsonlayer_upload_path(instance, filename):
    return unique_service_directory(instance, 'remote.json')


class GeoJsonLayer(BaseLayerMixin, StyleMixin, models.Model):
    url = models.CharField(max_length=100, null=True, blank=True)
    data_file = models.FileField(upload_to=geojsonlayer_upload_path,
                                 null=True, blank=True)
    service_path = models.CharField(max_length=255)
    cache_time = models.IntegerField(blank=True, null=True)
    last_fetch_on = models.DateTimeField(null=True, blank=True)
    generated_on = models.DateTimeField(null=True, blank=True)

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
        verbose_name = _('GeoJSONLayer')
        verbose_name_plural = _('GeoJSONLayers')


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


class DataBaseLayer(BaseLayerMixin, StyleMixin, models.Model):
    db_connection = models.ForeignKey(
        DBConnection, null=False, blank=False, on_delete=models.PROTECT,
        related_name='db_connections')
    slug = models.SlugField(max_length=255, blank=False, null=False,
                            unique=True)
    name = models.CharField(max_length=255, blank=False, null=False)

    table = models.CharField(max_length=255)
    pk_field = models.CharField(max_length=255, blank=False, null=False)
    geom_field = models.CharField(max_length=255, blank=False, null=False)

    class Meta:
        """Meta information."""
        verbose_name = 'DataBaseLayer'
        verbose_name_plural = 'DataBaseLayers'


@receiver(post_save, sender=DataBaseLayer)
def add_fields(sender, instance, created, **kwargs):
    if created:
        conn = instance.db_connection.get_connection()
        fields = model_legacy.get_fields(conn, instance.table)
        for field in fields:
            db_field = DataBaseLayerField()
            db_field.layer = instance
            db_field.field = field
            db_field.save()


class DataBaseLayerField(models.Model):
    layer = models.ForeignKey(
        DataBaseLayer, null=False, blank=False,
        related_name='fields')
    field = models.CharField(max_length=255, blank=False, null=False)
    alias = models.CharField(max_length=255, blank=True, null=True)
    enabled = models.BooleanField(default=True)

    def __unicode__(self):
        return self.__str__()

    def __str__(self):
        return self.alias or self.field

    class Meta:
        verbose_name = _('Field')
        verbose_name_plural = _('Fields')
