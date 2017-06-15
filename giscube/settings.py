"""
Django settings for giscube project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys
import logging
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPNAME = os.path.dirname(os.path.abspath(__file__))

APPURL = ''
APPURL = os.getenv('APPURL', APPURL)
SESSION_COOKIE_PATH = '%s/' % APPURL

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'c^y&lf98uw@ltecrs9s^_!7k7!&ent4i$k887)d&b@123ao*vp'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')
SSLIFY_DISABLE = os.getenv('DISABLE_SSL', 'True').lower() == 'true'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


GISCUBE_URL = os.environ.get('GISCUBE_URL',
                             'http://localhost:8080/apps/giscube')

GISCUBE_IMAGE_SERVER_ENABLED = os.environ.get('GISCUBE_IMAGE_SERVER_ENABLED',
                                              'False').lower() == 'true'
GISCUBE_GIS_SERVER_ENABLED = os.environ.get('GISCUBE_GIS_SERVER_ENABLED',
                                            'False').lower() == 'true'
GISCUBE_GEOPORTAL_ENABLED = os.environ.get('GISCUBE_GEOPORTAL_ENABLED',
                                           'False').lower() == 'true'


# Application definition
INSTALLED_APPS = [
    # app
    'giscube'
]

if GISCUBE_IMAGE_SERVER_ENABLED:
    INSTALLED_APPS += ['imageserver']
    GISCUBE_IMAGE_SERVER_URL = 'http://localhost/fcgis/giscube_imageserver/'
    GISCUBE_IMAGE_SERVER_URL = os.environ.get(
        'GISCUBE_IMAGE_SERVER_URL', GISCUBE_IMAGE_SERVER_URL)
    VAR_ROOT = os.path.join(BASE_DIR, 'var')
    VAR_ROOT = os.environ.get('GISCUBE_IMAGE_SERVER_VAR_ROOT', VAR_ROOT)
    VAR_URL = '%s/var/' % APPURL
    VAR_URL = os.environ.get('GISCUBE_IMAGE_SERVER_VAR_URL', VAR_URL)


if GISCUBE_GIS_SERVER_ENABLED:
    GISCUBE_QGIS_SERVER_URL = 'http://localhost/fcgis/giscube_qgisserver/'
    GISCUBE_QGIS_SERVER_URL = os.environ.get(
        'GISCUBE_QGIS_SERVER_URL', GISCUBE_QGIS_SERVER_URL)
    INSTALLED_APPS += ['qgisserver']

if GISCUBE_GEOPORTAL_ENABLED:
    INSTALLED_APPS += ['geoportal', 'haystack']
    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
            'PATH': os.path.join(BASE_DIR, 'var', 'whoosh_index'),
        },
    }

INSTALLED_APPS += [
    # django
    'django.contrib.gis',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'giscube.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': os.getenv('TEMPLATES', '').split(','),
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'giscube.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
         'ENGINE': 'django.contrib.gis.db.backends.postgis',
         'NAME': os.environ.get('DB_NAME', 'giscube'),
         'USER': os.environ.get('DB_USER', 'giscube'),
         'PASSWORD': os.environ.get('DB_PASSWORD', 'giscube'),
         'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
         'PORT': os.environ.get('DB_PORT', '5432'),
    },
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

MEDIA_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'media')
MEDIA_ROOT = os.getenv('MEDIA_ROOT', MEDIA_ROOT)
MEDIA_URL = '%s/media/' % APPURL

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_ROOT = os.getenv('STATIC_ROOT', STATIC_ROOT)


STATIC_URL = '%s/static/' % APPURL

# try:
#     import tilescache
#     if tilescache.giscube:
#         INSTALLED_APPS += ('tilescache',)
# except Exception, e:
#     print "[settings.py] tilescache not available: %s" % e
#     logger.exception(e)


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console', ],
        'level': 'INFO'
    },
}

# Overwrite settings
# -------------------------------------
ENVIRONMENT_NAME = os.environ.get('ENVIRONMENT_NAME', '')
extra_settings = 'settings-%s.py' % ENVIRONMENT_NAME
try:
    print "extra config from %s" % extra_settings
    execfile(os.path.join(BASE_DIR, APPNAME, extra_settings), globals())
except IOError, e:
    print e
    pass

# Covers regular testing and django-coverage
if 'test' in sys.argv or 'test_coverage' in sys.argv:
    DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'tests/media')
