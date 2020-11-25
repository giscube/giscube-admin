import zipfile

from django import forms
from django.utils.translation import gettext as _

from giscube.tilecache.admin_forms_mixins import TileCacheChangeFormMixin

from .models import Service


class ServiceChangeForm(TileCacheChangeFormMixin, forms.ModelForm):

    project = forms.FileField(required=False)

    def clean(self):
        super().clean()
        wms_buffer_enabled = self.cleaned_data['wms_buffer_enabled']
        tilecache_enabled = self.cleaned_data['tilecache_enabled']
        wms_single_image = self.cleaned_data['wms_single_image']

        if (wms_buffer_enabled or tilecache_enabled) and wms_single_image:
            msg = _("WMS single image' is not compatible with these options: 'WMS buffer enabled', 'Tilecache enabled")
            self.add_error('wms_single_image', msg)

        project = self.cleaned_data['project']
        if project and project.content_type not in ('application/x-qgis-project', 'application/zip'):
            raise forms.ValidationError(_('Only zip or qgs files are suported.'))
        if project and project.content_type == 'application/zip' and not zipfile.is_zipfile(project.file):
            raise forms.ValidationError(_('Invalid zipfile.'))
        if project and project.content_type == 'application/zip':
            zip_file = zipfile.ZipFile(project)
            name = '%s.qgs' % self.cleaned_data['name']
            if name not in zip_file.namelist():
                raise forms.ValidationError(_('There is not %s in %s' % (name, self.cleaned_data['project'].name)))

    class Meta:
        model = Service
        exclude = ()
