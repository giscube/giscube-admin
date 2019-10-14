#!/usr/bin/env bash

if [ -z "$1" ]
  then
    exec /usr/sbin/gosu "$DOCKER_USER" "/bin/bash"
else
    exec /usr/sbin/gosu "$DOCKER_USER" "$@"
fi
