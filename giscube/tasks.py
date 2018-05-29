# -*- coding: utf-8 -*-

from giscube.celery import app


def haystack_rebuild_index():
    from django.core.management import call_command
    call_command('rebuild_index', '--noinput')


@app.task
def async_haystack_rebuild_index():
    haystack_rebuild_index()
