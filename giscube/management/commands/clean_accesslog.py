import logging

from django.utils import timezone
from django.core.management.base import BaseCommand

from giscube.models import AccessLog


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean old access logs'

    def handle(self, *args, **options):
        today = timezone.now().date()
        
        deleted_count = AccessLog.objects.filter(
            accessed_date__lt=today
        ).delete()[0]
        
        message = f'Deleted {deleted_count} old access log entries.'
        logger.info(message)
