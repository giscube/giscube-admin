#!/usr/bin/env bash
set -e

exec /usr/sbin/gosu "$DOCKER_USER" "$@"
