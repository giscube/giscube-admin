import os
import textwrap

from model_utils import Choices

from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils.translation import gettext as _

from .languages import iso_639_choices
from .storage import OverwriteStorage


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
                            help_text='The format is: xmin,ymin,xmin,xmax. BBOX coordinates must be in EPSG:4326')

    def __str__(self):
        return textwrap.shorten(text=self.information or '', width=50, placeholder='...')

    class Meta:
        abstract = True


RESOURCE_TYPE_CHOICES = Choices(
    ('TMS', 'TMS'),
    ('WMS', 'WMS'),
    ('document', 'Document'),
    ('url', 'URL'),
)


def resource_upload_to(instance, filename):
    meta = instance.parent._meta
    parent_folder = '%s/%s' % (meta.app_label, meta.object_name.lower())
    return '%s/%s/resource/%s' % (parent_folder, instance.parent.pk, filename)


class ResourceModelMixin(models.Model):
    type = models.CharField(_('type'), max_length=12, choices=RESOURCE_TYPE_CHOICES)
    name = models.CharField(_('name'), max_length=50)
    description = models.TextField(_('description'), null=True, blank=True)
    title = models.CharField(_('title'), max_length=100, null=True, blank=True)
    path = models.CharField(_('path'), max_length=255, null=True, blank=True)
    url = models.CharField(_('url'), max_length=255, null=True, blank=True)
    file = models.FileField(_('file'), max_length=255, null=True, blank=True, upload_to=resource_upload_to,
                            storage=OverwriteStorage())
    layers = models.CharField(_('layers'), max_length=255, null=True, blank=True)
    projection = models.IntegerField(_('projection'), null=True, blank=True, help_text='EPSG code')
    getfeatureinfo_support = models.BooleanField(_('WMS GetFeatureInfo support'), default=True)
    single_image = models.BooleanField(_('use single image'), default=False)
    downloadable = models.BooleanField(_('downloadable'), default=False)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        if self.file:
            folder = os.path.dirname(self.file.name)
            self.file.delete(save=False)
            delete_parent = None
            if isinstance(self.file.storage, FileSystemStorage):
                dirs, files = self.file.storage.listdir(folder)
                if len(files) == 0:
                    delete_parent = os.path.join(self.file.storage.location, folder)
            if delete_parent is not None:
                os.rmdir(delete_parent)

    def __str__(self):
        return '%s' % self.title or self.name

    class Meta:
        abstract = True
