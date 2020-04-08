from django.contrib import admin
from django.utils.translation import gettext as _


class MetadataInlineMixin(admin.StackedInline):
    classes = ('tab-metadata',)
    verbose_name = _('Metadata')
    verbose_name_plural = _('Metadata')
    # FIX-ME: to_field fails
    # autocomplete_fields = ('category',)
