from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext as _

from giscube.utils import remove_app_url, url_slash_join


class WFSModelAdminMixin:
    def get_fieldsets(self, request, obj=None):
        if obj:
            obj._request = request

        fields = ['wfs_enabled']

        fieldsets = super().get_fieldsets(request, obj)
        if obj:
            fields.append('wfs_url')

        fields = fields + [
            'wfs_transaction_enabled',
        ]
        fieldsets.append(
            (None, {
                'fields': fields,
                'classes': ('tab-wfs',),
            })
        )

        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request)
        return list(readonly_fields) + ["wfs_url"]

    def wfs_url(self, obj):
        relative_url = reverse("qgisserver-wfs", args=(obj.name,))
        relative_url = remove_app_url(relative_url)
        return url_slash_join(settings.GISCUBE_URL, relative_url)
    wfs_url.short_description = _("WFS URL")
