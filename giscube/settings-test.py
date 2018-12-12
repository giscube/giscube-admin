DEBUG = True

DATABASES['default'] = {
    'ENGINE': 'django.contrib.gis.db.backends.postgis',
    'NAME': 'test',
    'USER': 'admin',
    'PASSWORD':  'admin',
    'HOST': '127.0.0.1',
    'PORT': '5432',
}

# https://www.caktusgroup.com/blog/2013/06/26/media-root-and-django-tests/
MEDIA_ROOT = os.path.join(BASE_DIR, 'tests', 'media')
MEDIA_URL = '/media/'

SECRET_KEY = os.getenv(
    'SECRET_KEY', 'c^y&lf98uw@ltecrs9s^_!7k7!&ent4i$k887)d&b@123ao*vp')


INSTALLED_APPS = INSTALLED_APPS + ['tests']
