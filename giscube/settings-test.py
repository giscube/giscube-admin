DEBUG = True

SPATIALITE_LIBRARY_PATH = 'mod_spatialite'

DATABASES['default'] = {
    'ENGINE': 'django.contrib.gis.db.backends.spatialite',
    'NAME': 'test.db'
}

# https://www.caktusgroup.com/blog/2013/06/26/media-root-and-django-tests/
MEDIA_ROOT = os.path.join(BASE_DIR, 'tests', 'media')
MEDIA_URL = '/media/'

SECRET_KEY = os.getenv(
    'SECRET_KEY', 'c^y&lf98uw@ltecrs9s^_!7k7!&ent4i$k887)d&b@123ao*vp')
