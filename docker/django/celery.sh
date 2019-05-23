#!/usr/bin/env bash

CELERY_LOG=/tmp/giscube_worker.log
celery worker -E -A giscube -l info -Q sequential_queue --concurrency=1 -f ${CELERY_LOG} & \
celery worker -E -A giscube -l info -Q default --concurrency=3 -f ${CELERY_LOG}
