# -*-  coding: utf-8 -*-
from django.core.management.base import BaseCommand
from giscube.tasks import async_test_send_email_admins


class Command(BaseCommand):
    help = 'test_send_email_admins celery example'

    def handle(self, *args, **options):

        res = async_test_send_email_admins.delay()
        print(res)
