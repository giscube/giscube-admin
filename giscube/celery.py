import json
import os

from datetime import datetime, timedelta
from urllib.parse import urlencode

import requests

from celery import Celery

from django.conf import settings
from django.contrib import messages
from django.db import models
from django.shortcuts import render
from django.urls import path
from django.utils.translation import gettext as _


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'giscube.settings')

app = Celery('proj')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


# https://github.com/jezdez/django-celery-monitor/issues/53

app.conf.monitors_expire_success = timedelta(days=7)
app.conf.monitors_expire_error = timedelta(days=7)
app.conf.monitors_expire_pending = timedelta(days=7)


class CeleryConnectionError(Exception):
    pass


def get_celery_tasks(hours=None):
    if not hours:
        hours = settings.CELERY_REPORT_FINISHED_TASKS_TIME
    date_start = datetime.now() - timedelta(hours=hours)
    query_args = urlencode({
        "received_start": date_start.strftime('%Y-%m-%d %H:%M'),
        "sort_by": "-received",
    })
    endpoint = f"{settings.CELERY_FLOWER_API}/api/tasks"
    url = f"{endpoint}?{query_args}"
    try:
        flower_response = requests.get(
            url, auth=(settings.FLOWER_USER, settings.FLOWER_PASSWORD)
        )
        if flower_response.status_code != 200:
            error_message = _(
                "Error %(status_code)s fetching background tasks from Flower API at %(url)s."
            ) % {
                "url": settings.CELERY_FLOWER_API,
                "status_code": flower_response.status_code,
            }

            raise CeleryConnectionError(error_message)

        return flower_response.json()

    except ConnectionError as e:
        error_message = _(
            "Cannot connect to Flower API at %(url)s. Please check that Celery and Flower API are running."
        ) % {"url": settings.CELERY_FLOWER_API}

        raise CeleryConnectionError(error_message) from e

    except json.JSONDecodeError as e:
        error_message = _(
            "The Flower API at %(url)s is not returning a JSON response."
        ) % {"url": settings.CELERY_FLOWER_API}

        raise CeleryConnectionError(error_message) from e


class HoursFilter(models.IntegerChoices):
    ONE = 1, "1"
    TWO = 2, "2"
    SIX = 6, "6"
    TWELVE = 12, "12"
    TWENTY_FOUR = 24, "24"
    FOURTY_EIGHT = 48, "48"


def background_task_monitoring(request):
    try:
        hours = request.GET.get("hours", None)
        hours = int(hours) if hours else hours
        tasks = get_celery_tasks(hours)

    except CeleryConnectionError as e:
        messages.error(request, str(e))
        tasks = {}

    for task_id, task_data in tasks.items():
        tasks[task_id]["finished"] = (
            task_data.get("succeeded")
            or task_data.get("failed")
            or task_data.get("revoked")
            or task_data.get("rejected")
        )
        date_fields = ["finished", "started", "received"]
        for field in date_fields:
            tasks[task_id][field] = (
                datetime.fromtimestamp(int(task_data.get(field)))
                if task_data.get(field)
                else None
            )

    return render(
        request,
        "admin/background_tasks.html",
        {"tasks": tasks, "hours": hours, "filter_options": HoursFilter.choices},
    )


urlpatterns = [
    path("tasks/", background_task_monitoring, name="background_tasks_monitoring"),
]
