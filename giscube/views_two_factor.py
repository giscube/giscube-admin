import json
import os

from datetime import timedelta
from uuid import uuid4

from two_factor.views import DisableView, SetupView, LoginView

from django.conf import settings
from django.template.response import SimpleTemplateResponse
from django.urls import reverse
from django.utils import timezone

from oauth2_provider.models import AccessToken, Application
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView


class Custom2FASetupView(SetupView):
    """Remove the 'Cancel' button from the 2FA setup view."""

    template_name = 'two_factor/core/setup.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = None
        return context


class Custom2FADisableView(DisableView):
    """2FA is mandatory, so disabling 2FA will redirect to the setup view directly."""

    template_name = 'two_factor/profile/disable.html'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.success_url = reverse('two_factor:setup')


class ClientLogin(APIView):
    template_name = 'giscube/client_post_message.html'
    authentication_classes = (SessionAuthentication,)
    permission_classes = (AllowAny,)

    def _get_token_for_user(self, user):
        try:
            application = Application.objects.get(name=settings.OAUTH2_GEOPORTAL_APPLICATION_NAME)

            now = timezone.now()
            at = AccessToken.objects.filter(user=user, application=application, expires__gt=now).first()
            if at:
                return at.token
            else:
                expires = now + timedelta(seconds=settings.OAUTH2_PROVIDER['ACCESS_TOKEN_EXPIRE_SECONDS'])
                at = AccessToken.objects.create(
                    user=user,
                    application=application,
                    token=str(uuid4()),
                    expires=expires,
                    scope='read write'
                )
                return at.token
        except Application.DoesNotExist:
            return None

    def get(self, request):
        context = {
            'type': 'serverLogin',
            'origins': settings.GISCUBE_GEOPORTAL_ORIGINS,
        }
        if request.user.is_authenticated:
            token = request.session.get('access_token', None)
            if not token:
                token = self._get_token_for_user(request.user)
            context.update({
                'title': 'Client Login Successful',
                'message': 'You have successfully logged in!',
                'user_info': json.dumps({
                    'username': request.user.username,
                    'access_token': token,
                })
            })
            # persist token in session so subsequent requests can reuse it
            if token:
                try:
                    request.session['access_token'] = token
                    request.session.modified = True
                except Exception:
                    pass
            return SimpleTemplateResponse(self.template_name, context=context)
        else:
            context.update({
                'title': 'Client Login Error',
                'message': 'There was a problem logging you in. Please try again or contact support if the issue persists.',
                'user_info': json.dumps(
                    {
                        'username': None,
                        'access_token': None,
                    }
                ),
            })
            return SimpleTemplateResponse(self.template_name, context=context)


class ClientLogout(APIView):
    """API endpoint to log out the user and return a confirmation."""

    template_name = "giscube/client_post_message.html"
    authentication_classes = (SessionAuthentication,)
    permission_classes = (AllowAny,)

    def get(self, request):
        if request.user.is_authenticated:
            from django.contrib.auth import logout
            logout(request)

        if 'access_token' in request.session:
            del request.session['access_token']
            request.session.modified = True

        context = {
            "title": "Client Logout Successful",
            "type": "serverLogout",
            "message": "You have successfully logged out!",
            "origins": settings.GISCUBE_GEOPORTAL_ORIGINS,
            "user_info": json.dumps(
                {
                    "username": None,
                    "access_token": None,
                }
            ),
        }
        return SimpleTemplateResponse(self.template_name, context=context)


class CustomLoginView(LoginView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["security_policy_url"] = os.environ.get("SECURITY_POLICY_URL")
        return context

    def get_success_url(self):
        if self.request.user.is_authenticated and settings.GISCUBE_ENABLE_2FA:
            from django_otp import devices_for_user
            if not list(devices_for_user(self.request.user)):
                return reverse('two_factor:setup')
        return super().get_success_url()
