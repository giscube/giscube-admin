from django.conf import settings
from django.forms import widgets
from django.utils.translation import get_language


class ColorWidget(widgets.TextInput):
    def __init__(self, attrs={}):
        attrs.update({'class': 'color-widget'})
        super().__init__(attrs)

    class Media:
        extra = '' if settings.DEBUG else '.min'
        js = ['vendors/bgrins-spectrum/spectrum%s.js' % extra, 'giscube/js/widgets/color.js']
        lang = get_language()
        if lang != 'en':
            js.insert(1, 'vendors/bgrins-spectrum/i18n/jquery.spectrum-%s.js' % lang)
        css = {
            'all': ('vendors/bgrins-spectrum/spectrum%s.css' % extra,)
        }
