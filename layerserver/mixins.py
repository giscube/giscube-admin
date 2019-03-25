# -*- coding: utf-8 -*-


from django.contrib.gis.db import models
from django.utils.translation import gettext as _
from django.conf import settings

from colorfield.fields import ColorField

from giscube.models import Category


SHAPE_TYPES_CHOICES = [
    ('marker', _('Marker')),
    ('line', _('Line')),
    ('polygon', _('Polygon')),
    ('Circle', _('Circle'))
]


class BaseLayerMixin(models.Model):
    """
    BaseLayer mixin.
    """
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    keywords = models.CharField(max_length=200, null=True, blank=True)
    active = models.BooleanField(default=True, help_text='Enable/disable usage')
    visible_on_geoportal = models.BooleanField(default=False)

    class Meta:
        abstract = True


class StyleMixin(models.Model):
    """
    Style mixin.
    """
    shapetype = models.CharField(blank=True, null=True, max_length=20,
                                 choices=SHAPE_TYPES_CHOICES)
    shape_radius = models.IntegerField(blank=True, null=True)
    stroke_color = ColorField(
        max_length=20, blank=True, null=True,
        default=settings.LAYERSERVER_STYLE_STROKE_COLOR)
    stroke_width = models.IntegerField(blank=True, null=True, default=1)
    stroke_dash_array = models.CharField(max_length=25, blank=True, null=True,
                                         default='')
    fill_color = ColorField(
        max_length=20, blank=True, null=True,
        default=settings.LAYERSERVER_STYLE_FILL_COLOR)
    fill_opacity = models.DecimalField(blank=True, null=True, default=1,
                                       max_digits=2, decimal_places=1)

    class Meta:
        abstract = True
