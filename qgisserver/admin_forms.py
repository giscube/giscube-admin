import zipfile

from django import forms
from django.utils.translation import gettext as _

from giscube.tilecache.admin_forms_mixins import TileCacheChangeFormMixin

from .models import Service, ServiceFilter


class ServiceChangeForm(TileCacheChangeFormMixin, forms.ModelForm):

    project = forms.FileField(required=False)

    def clean(self):
        super().clean()
        wms_buffer_enabled = self.cleaned_data['wms_buffer_enabled']
        tilecache_enabled = self.cleaned_data['tilecache_enabled']
        wms_single_image = self.cleaned_data['wms_single_image']
        tilecache_minzoom_level = self.cleaned_data['tilecache_minzoom_level']
        tilecache_maxzoom_level = self.cleaned_data['tilecache_maxzoom_level']
        tilecache_minZoom_level_chached = self.cleaned_data['tilecache_minZoom_level_chached']
        tilecache_maxZoom_level_chached = self.cleaned_data['tilecache_maxZoom_level_chached']

        if (wms_buffer_enabled or tilecache_enabled) and wms_single_image:
            msg = _("WMS single image' is not compatible with these options: 'WMS buffer enabled', 'Tilecache enabled")
            self.add_error('wms_single_image', msg)

        if tilecache_minzoom_level > tilecache_maxzoom_level:
            self.add_error('tilecache_minzoom_level', 'This field must be lower or equal than Maximum zoom level')
            self.add_error('tilecache_maxzoom_level', 'This field must be bigger or equal than Minimum zoom leve')

        if tilecache_minZoom_level_chached > tilecache_maxZoom_level_chached:
            self.add_error('tilecache_minZoom_level_chached', 'This field must be lower or equal than Max zoom level cached')
            self.add_error('tilecache_maxZoom_level_chached', 'This field must be bigger or equal than Min zoom level cached')

        project = self.cleaned_data['project']

        if project and project.content_type not in (
            'application/x-qgis-project',
            'application/zip',
            'application/x-zip-compressed',
            'application/octet-stream',
        ):
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


class ServiceFilterForm(forms.ModelForm):
    class Meta:
        model = ServiceFilter
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        layers_choices = kwargs.pop('layers_choices', [])
        super().__init__(*args, **kwargs)
        self.fields['layer'].widget = forms.Select(
            choices=[(l, l) for l in layers_choices]
        )
