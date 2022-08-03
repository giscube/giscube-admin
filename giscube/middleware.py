from oauth2_provider.middleware import OAuth2TokenMiddleware


class AccesTokenOAuth2TokenMiddleware(OAuth2TokenMiddleware):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if access_token := request.GET.get('access_token'):
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
            return super().__call__(request)

        response = self.get_response(request)

        return response
