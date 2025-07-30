
from django.conf import settings
from django.core.management.base import BaseCommand

from giscube.utils.django import clear_tokens_from_old_users, deactivate_old_users


class Command(BaseCommand):
    """
    (1) Deletes OAuth2 tokens for users inactive for 6+ months.
    (2) Deactivates users inactive for 1+ year (and removes staff status).
    """

    def handle(self, *args, **options):
        # Clear old tokens
        token_days = settings.MAX_REFRESH_TOKEN_DAYS
        inactive_users_count, deleted_access, deleted_refresh = (
            clear_tokens_from_old_users(token_days)
        )
        print(
            f"Deleted {deleted_access[0]} access tokens and {deleted_refresh[0]} refresh tokens "
            f"for {inactive_users_count} users inactive for {token_days} days."
        )

        # Deactivate old users
        inactive_days = settings.MAX_INACTIVE_USER_DAYS
        deactivated_count = deactivate_old_users(inactive_days)
        print(f"Deactivated {deactivated_count} users inactive for {inactive_days} days.")
