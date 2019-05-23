#!/usr/bin/env bash
set -e

DOCKER_DATA=/docker_data
DOCKER_USER=www-data

[ $(stat -c %U "$DOCKER_DATA") == "$DOCKER_USER" ] || chown -R "$DOCKER_USER" "$DOCKER_DATA"

exec /usr/sbin/gosu "$DOCKER_USER" "$@"
