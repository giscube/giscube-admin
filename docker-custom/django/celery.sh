#!/usr/bin/env bash
celery -A giscube worker -E -l info -Q sequential_queue --concurrency=1 &
celery -A giscube worker -E -l info -Q default --concurrency=3 &
celery -A giscube flower --address=0.0.0.0 --port=5555 --basic-auth="${FLOWER_USER}:${FLOWER_PASSWORD}"
