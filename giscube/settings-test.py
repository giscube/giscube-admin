DEBUG = True

CELERY_ALWAYS_EAGER = True

DATABASES['default'] = {
    'ENGINE': 'django.contrib.gis.db.backends.postgis',
    'NAME': 'test',
    'USER': 'admin',
    'PASSWORD':  'admin',
    'HOST': '127.0.0.1',
    'PORT': '5432',
}

MEDIA_ROOT = os.path.join('/tmp/', 'tests', 'media')
MEDIA_URL = '/media/'

SECRET_KEY = os.getenv(
    'SECRET_KEY', 'c^y&lf98uw@ltecrs9s^_!7k7!&ent4i$k887)d&b@123ao*vp')


INSTALLED_APPS = INSTALLED_APPS + ['tests']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    }
}
