from django.conf import settings


GISCUBE_SEARCH_DEFAULT_DICTIONARY = getattr(settings, 'GISCUBE_SEARCH_DEFAULT_DICTIONARY', 'english')
GISCUBE_SEARCH_MAX_RESULTS = getattr(settings, 'GISCUBE_SEARCH_MAX_RESULTS', None)
