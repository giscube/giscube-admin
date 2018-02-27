DEBUG = True

SPATIALITE_LIBRARY_PATH = 'mod_spatialite'

DATABASES['default'] = {
    'ENGINE': 'django.contrib.gis.db.backends.spatialite',
    'NAME': 'test.db'
}

# https://www.caktusgroup.com/blog/2013/06/26/media-root-and-django-tests/
MEDIA_ROOT = os.path.join(BASE_DIR, 'tests', 'media')
MEDIA_URL = '/media/'
