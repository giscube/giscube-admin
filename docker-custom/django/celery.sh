#!/usr/bin/env bash
celery worker -E -A giscube -l info -Q sequential_queue --concurrency=1 &
celery worker -E -A giscube -l info -Q default --concurrency=3
