#!/usr/bin/env bash

echo "runserver!!!!!"

exec python3 -Wall manage.py runserver 0.0.0.0:3000
