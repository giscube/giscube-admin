from urllib.parse import urlparse, parse_qs

from oauth2_provider.middleware import OAuth2TokenMiddleware


class AccesTokenOAuth2TokenMiddleware(OAuth2TokenMiddleware):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.META.get('HTTP_AUTHORIZATION', '').startswith('Bearer') and request.GET.get('access_token'):
            bearer = 'Bearer %s' % request.GET.get('access_token')
            request.META['HTTP_AUTHORIZATION'] = bearer

        if uri := request.META.get('REQUEST_URI'):
            url_parse = urlparse(uri)
            query_string = parse_qs(url_parse.query)
            if 'access_token' in query_string:
                bearer = 'Bearer %s' % query_string['access_token'][0]
                request.META['HTTP_AUTHORIZATION'] = bearer

        return super().__call__(request)
