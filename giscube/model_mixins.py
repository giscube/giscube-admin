import textwrap

from django.db import models
from django.utils.translation import gettext as _

from .languages import iso_639_choices


class MetadataModelMixin(models.Model):
    date = models.DateField(_('date'), blank=True, null=True)
    language = models.CharField(_('language'), choices=iso_639_choices, max_length=2, blank=True, null=True)
    category = models.ForeignKey(
        'giscube.MetadataCategory', to_field='code', blank=True, null=True, on_delete=models.SET_NULL,
        related_name='%(app_label)s_%(class)s_metadata')
    information = models.TextField(_('information'), blank=True, null=True)
    provider_name = models.CharField(_('provider name'), max_length=255, blank=True, null=True)
    provider_web = models.URLField(_('provider web'), max_length=255, blank=True, null=True)
    provider_email = models.CharField(_('provider email'), max_length=255, blank=True, null=True)
    summary = models.TextField(_('summary'), blank=True, null=True)
    bbox = models.CharField(_('BBOX'), max_length=255, blank=True, null=True,
    help_text='The format is: xmin,ymin,xmin,xmax. BBOX coordinates must be in EPSG:4326'
    )

    def __str__(self):
        return textwrap.shorten(text=self.information or '', width=50, placeholder='...')

    class Meta:
        abstract = True
