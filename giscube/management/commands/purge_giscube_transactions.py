from django.core.management.base import BaseCommand

from giscube.models import GiscubeTransaction


class Command(BaseCommand):
    help = 'Deletes old GiscubeTransaction objects'

    def handle(self, *args, **options):
        print('Purge old Giscube transactions')
        GiscubeTransaction.purge_old()
