from django.utils.translation import gettext as _

from giscube.admin_filters import NullFilterSpec


class DataBaseLayerGeomNullFilter(NullFilterSpec):
    title = _('Has geometry')
    parameter_name = 'geom_field'

    def lookups(self, request, model_admin):
        return (
            ('1', _('Yes'), ),
            ('0', _('No'), ),
        )
