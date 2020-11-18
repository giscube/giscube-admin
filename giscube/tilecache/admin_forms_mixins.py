from django import forms
from django.utils.translation import gettext as _


class TileCacheChangeFormMixin(forms.ModelForm):
    get_bbox_from_project = forms.BooleanField(label=_('Get BBOX from project'), required=False, initial=False)
    tilecache_clear_cache = forms.BooleanField(label=_('Clear cache'), required=False, initial=False)
