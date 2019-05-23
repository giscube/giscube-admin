#!/usr/bin/env bash

DOCKER_USER=www-data

exec /usr/sbin/gosu "$DOCKER_USER" "$@"
