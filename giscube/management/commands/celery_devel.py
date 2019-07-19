import os
import shlex
import subprocess

from django.core.management.base import BaseCommand
from django.utils import autoreload


def restart_celery():
    print('Restart celery devel workers')
    cmd = 'pkill -9 celery'
    subprocess.call(shlex.split(cmd))
    cmd = os.environ.get('CELERY_DEVEL_CMD')
    subprocess.call(shlex.split(cmd))


class Command(BaseCommand):
    def handle(self, *args, **options):
        print('Starting celery workers with autoreload...')
        autoreload.main(restart_celery)
