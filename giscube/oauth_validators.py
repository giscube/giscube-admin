from datetime import timedelta

from django.utils import timezone
from django.conf import settings

from oauth2_provider.oauth2_validators import OAuth2Validator


class CustomOAuth2Validator(OAuth2Validator):

    def save_bearer_token(self, token, request, *args, **kwargs):
        if (
            request.grant_type == "client_credentials"
            and request.client
            and request.client.user
        ):
            expires_in = token.get("expires_in") or settings.ACCESS_TOKEN_EXPIRE_SECONDS
            expires = timezone.now() + timedelta(
                seconds=expires_in
            )
            request.user = request.client.user
            self._create_access_token(expires, request, token)
        else:
            return super().save_bearer_token(
                token,
                request,
                *args,
                **kwargs
            )
