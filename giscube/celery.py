from __future__ import absolute_import, unicode_literals
import os
from datetime import timedelta

from celery import Celery

from django.conf import settings


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'giscube.settings')

app = Celery('proj')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


# https://github.com/jezdez/django-celery-monitor/issues/53

app.conf.monitors_expire_success = timedelta(days=7)
app.conf.monitors_expire_error = timedelta(days=7)
app.conf.monitors_expire_pending = timedelta(days=7)
