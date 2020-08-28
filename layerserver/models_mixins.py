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
        Category, verbose_name=_('category'), null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(_('name'), max_length=50, unique=True)
    title = models.CharField(_('title'), max_length=100, null=True, blank=True)
    description = models.TextField(_('description'), null=True, blank=True)
    keywords = models.CharField(_('keywords'), max_length=200, null=True, blank=True)
    active = models.BooleanField(_('active'), default=True, help_text='Enable/disable usage')
    visible_on_geoportal = models.BooleanField(_('visible on geoportal'), default=False)

    class Meta:
        abstract = True


class ClusterMixin(models.Model):
    """
    Cluster mixin.
    """
    cluster_enabled = models.BooleanField(
        _('enable cluster'), default=False, help_text=_('Enable/disable cluster usage.'))
    cluster_options = models.TextField(_('cluster options'), blank=True, null=True, help_text=_('JSON format.'))

    class Meta:
        abstract = True


class StyleMixin(models.Model):
    """
    Style mixin.
    """
    shape_radius = models.CharField(_('shape radius'), max_length=50, blank=True, null=True)
    stroke_color = models.CharField(_('stroke color'), max_length=50, blank=True, null=True)
    stroke_width = models.CharField(_('stroke width'), max_length=50, blank=True, null=True, default='1')
    stroke_opacity = models.CharField(_('stroke opacity'), max_length=50, blank=True, null=True, default='1')
    stroke_dash_array = models.CharField(_('stroke dash array'), max_length=50, blank=True, null=True, default='')
    fill_color = models.CharField(_('fill color'), max_length=50, blank=True, null=True)
    fill_opacity = models.CharField(_('fill opacity'), max_length=50, blank=True, null=True, default='1')
    icon_type = models.CharField(_('icon type'), max_length=100, blank=True, null=True,
                                 choices=(('fa', 'fa',), ('img', 'img',)))
    icon = models.CharField(_('icon'), max_length=255, blank=True, null=True)
    icon_color = models.CharField(_('icon color'), max_length=50, blank=True, null=True)

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
    help_text = '%s %s' % (_('Field between curly braces. e.g.'), '{%s}' % _('street'))
    popup = models.TextField(_('popup'), blank=True, null=True, help_text=help_text)
    interactive = models.BooleanField(_('interactive'), default=True)

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


class TooltipMixin(models.Model):
    """
    Tooltip mixin.
    """
    help_text = '%s %s' % (_('Field between curly braces. e.g.'), '{%s}' % _('street'))
    tooltip = models.TextField(_('tooltip'), blank=True, null=True, help_text=help_text)

    class Meta:
        abstract = True
