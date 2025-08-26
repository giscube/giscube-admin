from typing import Dict
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext as _

from oauth2_provider.middleware import OAuth2TokenMiddleware

from giscube.celery import CeleryConnectionError, get_celery_tasks


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


class CheckRunningCeleryTasksMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __get_tasks_counters(self, tasks: Dict):
        running_task_states = ["STARTED", "RECEIVED", "RETRY", "PENDING"]
        finished_task_states = ["SUCCESS", "FAILURE", "REVOKED"]
        running_counter = 0
        finished_counter = 0
        failure_counter = 0
        for task_data in tasks.values():
            if task_data.get("state") in running_task_states:
                running_counter += 1
            elif task_data.get("state") in finished_task_states:
                finished_counter += 1
                if task_data.get("state") == "FAILURE":
                    failure_counter += 1

        return running_counter, finished_counter, failure_counter

    def __call__(self, request):
        is_django_admin_page = (
            request.path.startswith('/admin/') or
            request.path.startswith('/apps/giscube-admin/admin/')
        )
        is_staff_user = hasattr(request, 'user') and request.user.is_staff
        using_flower = bool(settings.CELERY_FLOWER_API)
        if not is_django_admin_page or not is_staff_user or not using_flower:
            return self.get_response(request)

        existing_messages = [str(m) for m in messages.get_messages(request)]

        try:
            tasks = get_celery_tasks()

        except CeleryConnectionError as e:
            # Avoid duplicated messages
            if str(e) not in existing_messages:
                messages.error(request, str(e))
            return self.get_response(request)

        message_status = "info"
        running, finished, failed = self.__get_tasks_counters(tasks)
        if failed > 0:
            message_status = "error"

        message_list = []
        if running > 0:
            message_list.append(
                _("%(running)d %(task_label)s running in the background.")
                % {
                    "running": running,
                    "task_label": _("task") if running == 1 else _("tasks"),
                }
            )

        if finished > 0:
            message_list.append(
                _("%(finished)d %(task_label)s finished (%(failed)d failed).")
                % {
                    "finished": finished,
                    "task_label": _("task") if finished == 1 else _("tasks"),
                    "failed": failed,
                }
            )

        is_task_monitoring_page = request.path.endswith("/admin/celery/tasks/")
        has_content = running != 0 or finished != 0
        if not is_task_monitoring_page and has_content:
            url = reverse("background_tasks_monitoring")
            message_list.append("<br>")
            message_list.append(
                _("View %(more_details)s.")
                % {
                    "more_details": '<a href="%s">%s</a>' % (url, _("more details")),
                }
            )

        info_message = " ".join(message_list)
        # Avoid duplicated messages
        if info_message and info_message not in existing_messages:
            method = getattr(messages, message_status, "info")
            method(request, info_message)

        return self.get_response(request)
