from django import forms

from giscube.tilecache.admin_forms_mixins import TileCacheChangeFormMixin

from .models import Service


class ServiceChangeForm(TileCacheChangeFormMixin, forms.ModelForm):
    class Meta:
        model = Service
        exclude = ()
