#!/usr/bin/env bash
celery -A giscube worker -E -l info -Q sequential_queue --concurrency=1 &
celery -A giscube worker -E -l info -Q default --concurrency=3
