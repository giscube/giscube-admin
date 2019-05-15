from django.contrib.admin.filters import SimpleListFilter
from django.utils.translation import gettext as _


class NullFilterSpec(SimpleListFilter):
    title = ''
    parameter_name = ''

    def lookups(self, request, model_admin):
        return (
            ('1', _('Has value'), ),
            ('0', _('None'), ),
        )

    def queryset(self, request, queryset):
        kwargs = {
            '%s' % self.parameter_name: None,
        }
        if self.value() == '0':
            return queryset.filter(**kwargs)
        if self.value() == '1':
            return queryset.exclude(**kwargs)
        return queryset
