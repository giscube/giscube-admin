from django import forms
from django.utils.translation import gettext as _

from giscube.tilecache.admin_forms_mixins import TileCacheChangeFormMixin

from .models import Service


class ServiceChangeForm(TileCacheChangeFormMixin, forms.ModelForm):

    def clean(self):
        super().clean()
        wms_buffer_enabled = self.cleaned_data['wms_buffer_enabled']
        tilecache_enabled = self.cleaned_data['tilecache_enabled']
        wms_single_image = self.cleaned_data['wms_single_image']

        if (wms_buffer_enabled or tilecache_enabled) and wms_single_image:
            msg = _("WMS single image' is not compatible with these options: 'WMS buffer enabled', 'Tilecache enabled")
            self.add_error('wms_single_image', msg)

    class Meta:
        model = Service
        exclude = ()
