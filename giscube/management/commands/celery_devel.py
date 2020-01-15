import os
import shlex
import subprocess

from django.core.management.base import BaseCommand


def restart_celery():
    print('Restart celery devel workers')
    cmd = 'pkill -9 celery'
    subprocess.call(shlex.split(cmd))
    cmd = os.environ.get('CELERY_DEVEL_CMD')
    subprocess.call(shlex.split(cmd))


class Command(BaseCommand):
    def handle(self, *args, **options):
        print('Starting celery workers with autoreload...')

        try:
            from django.utils.autoreload import run_with_reloader
            run_with_reloader(restart_celery)
        except ImportError:
            from django.utils import autoreload
            autoreload.main(restart_celery)
