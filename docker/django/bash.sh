#!/usr/bin/env bash

DOCKER_USER=www-data

if [ -z "$1" ]
  then
    exec /usr/sbin/gosu "$DOCKER_USER" "/bin/bash"
else
    exec /usr/sbin/gosu "$DOCKER_USER" "$@"
fi
