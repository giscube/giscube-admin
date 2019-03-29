from oauth2_provider.middleware import OAuth2TokenMiddleware


class AccesTokenOAuth2TokenMiddleware(OAuth2TokenMiddleware):
    def process_request(self, request):
        if not request.META.get('HTTP_AUTHORIZATION', '').startswith('Bearer') and \
                request.GET.get('access_token'):
            bearer = 'Bearer %s' % request.GET.get('access_token')
            request.META['HTTP_AUTHORIZATION'] = bearer
        super().process_request(request=request)
