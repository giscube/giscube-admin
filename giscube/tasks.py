# -*- coding: utf-8 -*-

from giscube.celery import app


@app.task
def async_test_send_email_admins():
    from django.core.mail import mail_admins
    mail_admins('async_test_send_email_admins', 'EMAIL for test celery')


def haystack_rebuild_index():
    from django.core.management import call_command
    call_command('rebuild_index', '--noinput')


@app.task(queue='sequential_queue')
def async_haystack_rebuild_index():
    haystack_rebuild_index()
