#!/usr/bin/env bash

cp /app/docker-custom/postgres/dictionaries/dist/ca.affix /usr/share/postgresql/12/tsearch_data/
cp /app/docker-custom/postgres/dictionaries/dist/ca.dict /usr/share/postgresql/12/tsearch_data/
cp /app/docker-custom/postgres/dictionaries/dist/catalan.stop /usr/share/postgresql/12/tsearch_data/

PGPASSWORD="${DB_PASSWORD}" psql -hlocalhost -U${DB_USER} --set ON_ERROR_STOP=on ${DB_NAME} < /app/docker-custom/postgres/dictionaries/catalan.sql
