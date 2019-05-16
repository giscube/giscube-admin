from django.conf import settings
from django.contrib.gis.db import models
from django.utils.translation import gettext as _

from giscube.models import Category


SHAPE_TYPES_CHOICES = [
    ('marker', _('Marker')),
    ('line', _('Line')),
    ('polygon', _('Polygon')),
    ('circle', _('Circle')),
    ('image', _('Image'))
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
    shape_radius = models.CharField(max_length=50, blank=True, null=True)
    stroke_color = models.CharField(max_length=50, blank=True, null=True,
                                    default=settings.LAYERSERVER_STYLE_STROKE_COLOR)
    stroke_width = models.CharField(max_length=50, blank=True, null=True, default='1')
    stroke_dash_array = models.CharField(max_length=50, blank=True, null=True, default='')
    fill_color = models.CharField(max_length=50, blank=True, null=True,
                                  default=settings.LAYERSERVER_STYLE_FILL_COLOR)
    fill_opacity = models.CharField(max_length=50, blank=True, null=True, default='1')
    marker_color = models.CharField(max_length=50, blank=True, null=True)
    icon_type = models.CharField(max_length=100, blank=True, null=True, choices=(('fa', 'fa',), ('img', 'img',)))
    icon = models.CharField(max_length=255, blank=True, null=True)
    icon_color = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        abstract = True


class ShapeStyleMixin(StyleMixin):
    """
    Style mixin.
    """
    shapetype = models.CharField(_('Shape Type'), blank=True, null=True, max_length=20, choices=SHAPE_TYPES_CHOICES)

    class Meta:
        abstract = True


class PopupMixin(models.Model):
    """
    Popup mixin.
    """
    popup = models.TextField(blank=True, null=True)

    def get_default_popup_content(self, fields):
        content = []
        list_fields = list(fields.items())
        if len(list_fields) > 0:
            content.append('<table>')
            for name, label in list(fields.items()):
                content.append('<tr><th>%s</th><td>{%s}</td></tr>' % (label, name))
            content.append('</table>')
        return '\n'.join(content)

    class Meta:
        abstract = True
