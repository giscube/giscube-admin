#!/usr/bin/env bash

PGPASSWORD="${DB_PASSWORD}" psql -hlocalhost -U${DB_USER} --set ON_ERROR_STOP=on ${DB_NAME} < docker/db/dictionaries/catalan.sql
