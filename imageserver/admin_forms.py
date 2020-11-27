from django import forms
from django.utils.translation import gettext as _

from giscube.tilecache.admin_forms_mixins import TileCacheChangeFormMixin

from .models import Service


class ServiceChangeForm(TileCacheChangeFormMixin, forms.ModelForm):
    project = forms.FileField(required=False)

    def clean(self):
        super().clean()
        tilecache_enabled = self.cleaned_data['tilecache_enabled']
        wms_single_image = self.cleaned_data['wms_single_image']

        if tilecache_enabled and wms_single_image:
            msg = _("WMS single image' is not compatible with 'Tilecache enabled")
            self.add_error('wms_single_image', msg)

    class Meta:
        model = Service
        exclude = ()
