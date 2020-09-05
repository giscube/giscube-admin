import hashlib

from functools import WRAPPER_ASSIGNMENTS, wraps
from traceback import format_tb

from django.http.response import HttpResponse, HttpResponseBadRequest

from .models import GiscubeTransaction


class GiscubeTransactionCacheResponse:
    def __call__(self, func):
        this = self

        @wraps(func, assigned=WRAPPER_ASSIGNMENTS)
        def inner(self, request, *args, **kwargs):
            return this.process_cache_response(
                view_instance=self,
                view_method=func,
                request=request,
                args=args,
                kwargs=kwargs,
            )
        return inner

    def log_transaction(self, request, response=None, error=None):
        request_headers = {k: v for k, v in request.META.items() if 'wsgi' not in k}
        user = request.user.username or str(request.user)
        data = {
            'hash': request.META.get('HTTP_X_BULK_HASH'),
            'user': user,
            'url': request.build_absolute_uri(),
            'request_headers': request_headers,
            'request_body': request.body
        }
        if response:
            response_headers = response._headers.copy()
            response_body = None
            if response.rendered_content:
                response_body = response.rendered_content
                if type(response_body) is bytes:
                    response_body = response_body.decode('utf-8')
            data.update({
                'response_headers': response_headers,
                'response_body': response_body,
                'response_status_code': response.status_code
            })
        if error:
            data.update({
                'response_status_code': 500,
                'error': error
            })
        GiscubeTransaction(**data).save()

    def process_cache_response(self, view_instance, view_method, request, args, kwargs):
        body = request.body
        if type(body) is str:
            body = body.encode('utf-8')
        hash = hashlib.md5(body).hexdigest()
        bulk_hash_meta = request.META.get('HTTP_X_BULK_HASH')
        if bulk_hash_meta and (hash != bulk_hash_meta):
            return HttpResponseBadRequest('INVALID X-Bulk-Hash')
        filter = {
            'hash': bulk_hash_meta
        }
        transaction = GiscubeTransaction.objects.filter(**filter).first()
        if not transaction:
            response = None
            error = None
            try:
                response = view_method(view_instance, request, *args, **kwargs)
            except Exception as e:
                error = '\n'.join(format_tb(e.__traceback__))
                raise
            finally:
                self.log_transaction(request, response=response, error=error)

        else:
            response = HttpResponse(content=transaction.response_body, status=transaction.response_status_code)
            for k, v in transaction.response_headers.values():
                response[k] = v

        if not hasattr(response, '_closable_objects'):
            response._closable_objects = []

        return response


giscube_transaction_cache_response = GiscubeTransactionCacheResponse
