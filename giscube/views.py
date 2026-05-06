import json
import mimetypes
import os

from datetime import timedelta
from uuid import uuid4

from two_factor.views import DisableView, SetupView, LoginView

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import FileResponse, Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.template.response import SimpleTemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.cache import patch_response_headers
from django.utils.encoding import force_str
from django.views.decorators.cache import never_cache
from django.views.static import serve

from django_otp import devices_for_user
from oauth2_provider.models import AccessToken, Application
from oauth2_provider.views import TokenView
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from geoportal.views import GeoportalMixin
from giscube.api_search_views import FilterByUserMixin

from .models import UserAsset


class CustomTokenView(TokenView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            try:
                response_data = json.loads(response.content.decode('utf-8'))
                if 'access_token' in response_data:
                    access_token = AccessToken.objects.get(
                        token=response_data['access_token']
                    )
                    if access_token.user:
                        access_token.user.last_login = timezone.now()
                        access_token.user.save(update_fields=['last_login'])

            except Exception as e:
                print(f"Error update last_login: {e}")

        return response


def media_user_asset(request, user_id, filename):
    if request.user:
        user = get_object_or_404(get_user_model(), pk=user_id)
        if request.user == user:
            path = 'user/assets/%s/%s' % (user_id, filename)
            asset = get_object_or_404(UserAsset, user_id=user_id, file=path)
            full_path = asset.file.path
            fd = open(full_path, 'rb')
            file_mime = mimetypes.guess_type(asset.file.name.split('/')[-1])
            response = FileResponse(fd, content_type=file_mime)
            patch_response_headers(response, cache_timeout=60 * 60 * 24 * 7)
            return response

    raise Http404


def private_serve(request, path):
    document_root = settings.MEDIA_ROOT
    show_indexes = False
    if request.user and request.user.is_superuser:
        return serve(request, path, document_root, show_indexes)
    return HttpResponseForbidden()


def web_map_view(request, extra_context):
    """
    Context requires:
    layer_url
    layer_type: tile | wms
    bbox
    base_layer as LEAFLET_CONFIG.TILES
    title
    """

    context = {
        'LEAFLET_CONFIG': {'TILES': 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'}
    }
    context.update(extra_context)
    return render(request, 'admin/giscube/web_map.html', context)


class ResourceFileServer(GeoportalMixin, FilterByUserMixin, APIView):

    def get(self, request, module, model, pk, file):
        allowed = {
            'giscube': ['dataset'],
            'imageserver': ['service'],
            'qgisserver': ['service'],
            'layerserver': ['databaselayer', 'geojsonlayer'],
        }
        if not(model in allowed.get(module, [])):
            return HttpResponseForbidden()

        qs = self.get_model().objects
        qs = qs.filter(content_type='%s.%s' % (module, model), object_id=force_str(pk))
        qs = self.filter_by_user(request, qs)
        if not qs.exists():
            return HttpResponseForbidden()

        document_root = settings.MEDIA_ROOT
        show_indexes = False
        path = os.path.join(module, model, force_str(pk), 'resource', file)
        return serve(request, path, document_root, show_indexes)


@never_cache
def is_authenticated(request):
    success = request.user.is_authenticated
    if success:
        return HttpResponse('true')
    else:
        return HttpResponseForbidden()


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
        if self.request.user.is_authenticated:
            if not list(devices_for_user(self.request.user)):
                return reverse('two_factor:setup')
        return super().get_success_url()
