from django.views.decorators.debug import sensitive_variables


class APIHideAccessTokenMixin(object):
    @sensitive_variables('access_token')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
