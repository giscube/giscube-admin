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


class TagsWidget(widgets.Textarea):
    def __init__(self, attrs={}):
        attrs.update({'class': 'tags-widget'})
        super().__init__(attrs)

    class Media:
        extra = '' if settings.DEBUG else '.min'
        js = [
            'vendors/tagify/tagify%s.js' % extra,
            'vendors/sortable/Sortable%s.js' % extra,
            'giscube/js/widgets/tags.js']
        css = {
            'all': ('vendors/tagify/tagify.css',)
        }
