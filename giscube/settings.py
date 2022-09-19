"""
Django settings for giscube project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""
import logging
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import re
import sys

from corsheaders.defaults import default_headers
from kombu import Exchange, Queue

from django.utils.translation import gettext_lazy as _


logger = logging.getLogger(__name__)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.abspath(os.path.dirname(BASE_DIR))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

SSLIFY_DISABLE = os.getenv('DISABLE_SSL', 'True').lower() == 'true'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

GIS_SERVER_DEFAULT_WMS_VERSION = os.environ.get('GIS_SERVER_DEFAULT_WMS_VERSION',
                                                '1.3.0')
IMAGE_SERVER_DEFAULT_WMS_VERSION = os.environ.get('IMAGE_SERVER_DEFAULT_WMS_VERSION',
                                                  '1.3.0')

GISCUBE_URL = os.environ.get('GISCUBE_URL',
                             'http://localhost:8080/apps/giscube-admin')
GISCUBE_INTERNAL_URL = os.environ.get('GISCUBE_INTERNAL_URL', GISCUBE_URL)

GISCUBE_IMAGE_SERVER_DISABLED = os.environ.get('GISCUBE_IMAGE_SERVER_DISABLED',
                                               'False').lower() == 'true'
GISCUBE_GIS_SERVER_DISABLED = os.environ.get('GISCUBE_GIS_SERVER_DISABLED',
                                             'False').lower() == 'true'
GISCUBE_GEOPORTAL_DISABLED = os.environ.get('GISCUBE_GEOPORTAL_DISABLED',
                                            'False').lower() == 'true'

GISCUBE_LAYERSERVER_DISABLED = os.environ.get('GISCUBE_LAYERSERVER_DISABLED',
                                              'False').lower() == 'true'

# Application definition
INSTALLED_APPS = [
    'app_admin.apps.AppAdminConfig',
    # app
    'giscube.apps.GiscubeConfig',
    'giscube_search.apps.GiscubeSearchConfig',
    'geoportal',
    'corsheaders',
    'giscube.apps_titles.GiscubeOauth2ProviderConfig',  # 'oauth2_provider',
    'rest_framework',
    'loginas',
    'giscube.apps_titles.GiscubeCeleryResultConfig',  # 'django_celery_results',
    'django_admin_listfilter_dropdown',
    'django_db_logger',
]


INSTALLED_APPS += ['imageserver.apps.ImageServerConfig']
GISCUBE_IMAGE_SERVER_URL = 'http://localhost/fcgis/giscube_imageserver/'
GISCUBE_IMAGE_SERVER_URL = os.environ.get('GISCUBE_IMAGE_SERVER_URL', GISCUBE_IMAGE_SERVER_URL)


INSTALLED_APPS += ['qgisserver.apps.QGisServerConfig']
if not GISCUBE_GIS_SERVER_DISABLED:
    GISCUBE_QGIS_SERVER_URL = 'http://localhost/fcgis/giscube_qgisserver/'
    GISCUBE_QGIS_SERVER_URL = os.environ.get(
        'GISCUBE_QGIS_SERVER_URL', GISCUBE_QGIS_SERVER_URL)


if not GISCUBE_LAYERSERVER_DISABLED:
    INSTALLED_APPS += ['colorfield', 'layerserver.apps.LayerServerConfig', 'layerserver_databaselayer']


INSTALLED_APPS += [
    'theme_giscube',
    'django_vue_tabs',

    'leaflet',
    'sql_compiler',

    # django
    'django.contrib.gis',
    'django.contrib.admin',
    'django.contrib.auth',
    'groupadmin_users',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # cors headers
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'giscube.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': list(filter(None, os.getenv('TEMPLATES', '').split(','))),
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
        'ENGINE': 'giscube.db.backends.postgis',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

# General
# DEBUG defaults to False if not defined in the environment
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = list(filter(None, os.getenv('ALLOWED_HOSTS', '').split(',')))

# e.g.: My name,admin@example.com,Other admin,admin2@example.com
# ADMINS will be an empty array is it is not defined in the environment
ADMINS = list(zip(*([iter(os.getenv('ADMINS', '').split(','))] * 2))) if os.getenv('ADMINS', '') != '' else []

LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', LANGUAGE_CODE)

LOCALE_PATHS = ['locale'] + list(filter(None, os.getenv('LOCALE_PATHS', '').split(',')))

TIME_ZONE = 'UTC'
TIME_ZONE = os.getenv('TIME_ZONE', TIME_ZONE)

USE_I18N = True

USE_L10N = True

USE_TZ = True

ADMIN_SITE_HEADER = os.getenv('ADMIN_SITE_HEADER', 'GISCube')
ADMIN_SITE_TITLE = os.getenv('ADMIN_SITE_TITLE', 'GISCube Admin')
ADMIN_INDEX_TITLE = os.getenv('ADMIN_INDEX_TITLE', 'GISCube Admin')

APP_NAME = os.path.dirname(os.path.abspath(__file__))
APP_NAME = os.getenv('APP_NAME', APP_NAME)

APP_URL = '/%s/' % APP_NAME
APP_URL = os.getenv('APP_URL', APP_URL)
APP_ROOT = os.getenv('APP_PATH', BASE_DIR)

SITE_URL = os.getenv('SITE_URL', 'http://localhost')
SITE_INTERNAL_URL = os.getenv('SITE_INTERNAL_URL', SITE_URL)

LOGIN_URL = '%s/admin/login/' % APP_URL
LOGIN_REDIRECT_URL = '%s/admin/' % APP_URL

MEDIA_URL = '%s/media/' % APP_URL
MEDIA_URL = os.getenv('MEDIA_URL', MEDIA_URL)
MEDIA_ROOT = os.path.join(APP_ROOT, 'media')
MEDIA_ROOT = os.getenv('MEDIA_ROOT', MEDIA_ROOT)

STATIC_URL = '%s/static/' % APP_URL
STATIC_URL = os.getenv('STATIC_URL', STATIC_URL)
STATIC_ROOT = os.path.join(APP_ROOT, 'static')
STATIC_ROOT = os.getenv('STATIC_ROOT', STATIC_ROOT)

VAR_URL = '%s/var/' % APP_URL
VAR_URL = os.environ.get('VAR_URL', VAR_URL)
VAR_ROOT = os.path.join(APP_ROOT, 'var')
VAR_ROOT = os.environ.get('VAR_ROOT', VAR_ROOT)

SESSION_COOKIE_NAME = 'sessionid_%s' % APP_URL.replace('/', '_')
SESSION_COOKIE_PATH = '%s/' % APP_URL

IS_AUTHENTICATED_DISABLED = os.environ.get('IS_AUTHENTICATED_DISABLED', 'False').lower() == 'true'

# corsheaders
CORS_ORIGIN_ALLOW_ALL = os.getenv('CORS_ORIGIN_ALLOW_ALL',
                                  'False').lower() == 'true'
CORS_ORIGIN_WHITELIST = tuple(
    whitelisted
    for whitelisted
    in re.sub(r'\s', '', os.getenv('CORS_ORIGIN_WHITELIST', '')).split(',')
    if whitelisted
)
# CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = list(default_headers) + [
    'x-bulk-hash',
]

GISCUBE_IMAGESERVER = {
    'DATA_ROOT': os.environ.get('GISCUBE_IMAGESERVER_DATA_ROOT', os.path.join(APP_ROOT, 'imageserver')).split(',')
}

USE_CAS = os.getenv('USE_CAS', 'False').lower() == 'true'

if USE_CAS:

    INSTALLED_APPS += (
        'django_cas_ng',
    )

    needle = 'django.contrib.auth.middleware.AuthenticationMiddleware'
    index = MIDDLEWARE.index(needle)
    cas_middleware = 'django_cas_ng.middleware.CASMiddleware'
    MIDDLEWARE.insert(index + 1, cas_middleware)

    AUTHENTICATION_BACKENDS = [
        'django.contrib.auth.backends.ModelBackend',
        'django_cas_ng.backends.CASBackend',
    ]

    CAS_SERVER_URL = os.getenv('CAS_SERVER_URL', 'CAS_SERVER_URL not defined')
    CAS_REDIRECT_URL = '%s' % APP_URL
    CAS_CREATE_USER = False
    CAS_LOGOUT_COMPLETELY = True
    CAS_VERSION = 3

    LOGIN_URL = '%s/accounts/login/' % APP_URL
    LOGOUT_URL = '%s/accounts/logout/' % APP_URL
    LOGIN_REDIRECT_URL = '%s' % APP_URL

# oauth-toolkit
if USE_CAS:
    AUTHENTICATION_BACKENDS = [
        'oauth2_provider.backends.OAuth2Backend',
    ] + AUTHENTICATION_BACKENDS
else:
    AUTHENTICATION_BACKENDS = [
        'oauth2_provider.backends.OAuth2Backend',
        'django.contrib.auth.backends.ModelBackend',
    ]

index = MIDDLEWARE.index('django.contrib.auth.middleware.'
                         'AuthenticationMiddleware')
MIDDLEWARE.insert(index + 1,
                  'giscube.middleware.AccesTokenOAuth2TokenMiddleware')

OAUTH2_PROVIDER = {
    'RESOURCE_SERVER_INTROSPECTION_URL': os.environ.get(
        'RESOURCE_SERVER_INTROSPECTION_URL'),
    'RESOURCE_SERVER_AUTH_TOKEN': os.environ.get(
        'RESOURCE_SERVER_AUTH_TOKEN'),
    'RESOURCE_SERVER_INTROSPECTION_CREDENTIALS': list(filter(None, os.getenv(
        'RESOURCE_SERVER_INTROSPECTION_CREDENTIALS', '').split(','))),

    'RESOURCE_SERVER_TOKEN_CACHING_SECONDS': 60 * 60 * 10,

    'ACCESS_TOKEN_EXPIRE_SECONDS': 60 * 60 * 24 * 365 * 10,
}

# rest-framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'giscube.permissions.PermissionNone',
    ],
    'DEFAULT_RENDERER_CLASSES': (
        # 'rest_framework.renderers.JSONRenderer',
        # 'rest_framework.renderers.BrowsableAPIRenderer',
        'drf_ujson.renderers.UJSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        # 'rest_framework.parsers.JSONParser',
        'drf_ujson.parsers.UJSONParser',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
}

DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440 * 10

# celery
CELERY_DEFAULT_QUEUE = 'default'
CELERY_TASK_DEFAULT_QUEUE = 'default'

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
BROKER_URL = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

CELERY_QUEUES = (
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('sequential_queue', Exchange('long'), routing_key='sequential_queue')
)
CELERY_ROUTES = {
    'giscube.tasks.async_haystack_rebuild_index': {
        'queue': 'sequential_queue'
    }
}

CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_TASK_TRACK_STARTED = True

USER_ASSETS_STORAGE_CLASS = 'django.core.files.storage.FileSystemStorage'

LAYERSERVER_FILE_STORAGE_CLASS = 'django.core.files.storage.FileSystemStorage'
LAYERSERVER_THUMBNAIL_STORAGE_CLASS = 'django.core.files.storage.FileSystemStorage'

LAYERSERVER_THUMBNAIL_WIDTH = 256
LAYERSERVER_THUMBNAIL_HEIGHT = 256

LAYERSERVER_MAX_PAGE_SIZE = int(os.getenv('LAYERSERVER_MAX_PAGE_SIZE', '1000'))
LAYERSERVER_PAGE_SIZE = int(os.getenv('LAYERSERVER_PAGE_SIZE', '50'))

if not GISCUBE_LAYERSERVER_DISABLED:
    LAYERSERVER_STYLE_STROKE_COLOR = '#FF3333'
    LAYERSERVER_STYLE_FILL_COLOR = '#FFC300'

    DATABASE_ROUTERS = ['layerserver.routers.DataBaseLayersRouter']

    INSTALLED_APPS += [
        'rest_framework_gis',
    ]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'giscube.utils.AdminEmailHandler'
        },
        'db_log': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django_db_logger.db_log_handler.DatabaseLogHandler'
        },
    },
    'loggers': {
        # django request
        'db': {
            'handlers': ['db_log'],
            'level': 'ERROR'
        },
        'django.request': {
            'handlers': ['mail_admins', 'mail_admins', 'db_log'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Tasks menu
ADMIN_TASKS_MENU = [
    {
        'url': 'rebuild_giscube_search_index',
        'reverse': True,
        'title': _('Rebuild Giscube Search cache')
    }
]
# LogEntry

GISCUBE_ENABLE_LOGENTRY = os.getenv('GISCUBE_ENABLE_LOGENTRY', 'false').lower() == 'true'

# GiscubeSearch settings
GISCUBE_SEARCH_DEFAULT_DICTIONARY = os.getenv('GISCUBE_SEARCH_DEFAULT_DICTIONARY', 'english')
GISCUBE_SEARCH_MAX_RESULTS = os.getenv('GISCUBE_SEARCH_MAX_RESULTS', None)

# Purge old GiscubeTransaction objects
PURGE_GISCUBETRANSACTIONS_UNIT = os.getenv('PURGE_GISCUBETRANSACTIONS_UNIT', 'days')
PURGE_GISCUBETRANSACTIONS_VALUE = int(os.getenv('PURGE_GISCUBETRANSACTIONS_VALUE', '30'))

# Giscube email message
GISCUBE = {
    'password_recovery_email_subject': os.getenv('GISCUBE_PASSWORD_RECOVERY_EMAIL_SUBJECT', 'Giscube password recovery'),
    'password_recovery_email_body': os.getenv('GISCUBE_PASSWORD_RECOVERY_EMAIL_BODY', 'Hi there,\n\n'
                                              'Your Giscube access is ready.\n\n'
                                              'Please enter this website: {{ site_url }}\n\n'
                                              'Your username is {{ username }}\n'
                                              'Your password can be set using this link: {{ activation_link }}\n\n'
                                              'Kind Regards,\n\n'
                                              'Your Giscube administrator')
}

# Email
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = os.getenv('EMAIL_PORT')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'true').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')

EMAIL_SUBJECT_PREFIX = '[%s] ' % APP_NAME
# From address for error messages
SERVER_EMAIL = os.getenv('SERVER_EMAIL', '')

# sentry

SENTRY_DSN = os.getenv('SENTRY_DSN', None)
if SENTRY_DSN is not None:
    import sentry_sdk

    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()]
    )

# Plugins
GISCUBE_PLUGINS_PATH = os.environ.get('GISCUBE_PLUGINS_PATH', None)
GISCUBE_PLUGINS = list(filter(None, os.environ.get('GISCUBE_PLUGINS', '').split(',')))

if GISCUBE_PLUGINS_PATH:
    for plugin in GISCUBE_PLUGINS:
        path = os.path.join(GISCUBE_PLUGINS_PATH, plugin, 'src')
        sys.path.append(path)
        INSTALLED_APPS.append(plugin)
        settings_plugin_path = os.path.join(path, plugin, 'settings.py')
        if os.path.isfile(settings_plugin_path):
            with open(settings_plugin_path, 'rb') as f:
                exec(compile(f.read(), settings_plugin_path, 'exec'), globals())

# Overwrite settings
# -------------------------------------
ENVIRONMENT_NAME = os.environ.get('ENVIRONMENT_NAME', '')
extra_settings_file = 'settings-%s.py' % ENVIRONMENT_NAME
extra_settings_dir = os.path.dirname(os.path.abspath(__file__))
extra_settings_path = os.path.join(extra_settings_dir, extra_settings_file)
if os.path.isfile(extra_settings_path):
    print('Try to load extra settings: %s' % extra_settings_file)
    # Python 2 only:
    # execfile(extra_settings_path, globals())
    # Python 2 and 3:
    with open(extra_settings_path, 'rb') as f:
        exec(compile(f.read(), extra_settings_path, 'exec'), globals())

CUSTOM_SETTINGS_FILE = os.environ.get('CUSTOM_SETTINGS_FILE', None)
if CUSTOM_SETTINGS_FILE and os.path.isfile(CUSTOM_SETTINGS_FILE):
    print('Try to load extra settings: %s' % CUSTOM_SETTINGS_FILE)
    with open(CUSTOM_SETTINGS_FILE, 'rb') as f:
        exec(compile(f.read(), CUSTOM_SETTINGS_FILE, 'exec'), globals())
