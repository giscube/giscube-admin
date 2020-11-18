#!/usr/bin/env bash

DB_NAME=giscube_data
DB_USER=giscube_data

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

if [[ ${ENVIRONMENT_NAME} = "devel" ]]
  then
    echo "Devel environment, proceeding..."
  else
    echo "Not in devel environment :(, exiting"
    exit 1
fi

SUDO="su postgres -c "

# Standard
echo "- Create database ${DB_NAME}"

$SUDO 'psql <<EOF
CREATE DATABASE "${DB_NAME}";
EOF
'

echo "- Create role ${DB_USER}"
$SUDO 'psql ${DB_NAME} <<EOF
CREATE ROLE "${DB_USER}" LOGIN;
EOF
'

echo "- Set role ${DB_USER} password to ${DB_PASSWORD}'"
$SUDO "psql ${DB_NAME} <<EOF
ALTER ROLE \"${DB_USER}\" WITH PASSWORD '${DB_PASSWORD}';
EOF
"

echo "- Set role ${DB_USER} permissions SUPERUSER CREATEDB'"
$SUDO "psql ${DB_NAME} <<EOF
ALTER ROLE \"${DB_USER}\" SUPERUSER CREATEDB;
EOF
"

echo "- CREATE SCHEMA ${DB_USER};" ${DB_NAME}
$SUDO "psql ${DB_NAME} <<EOF
CREATE SCHEMA \"${DB_USER}\" AUTHORIZATION \"${DB_USER}\"; GRANT ALL ON SCHEMA \"${DB_USER}\" TO \"${DB_USER}\";
EOF
"

echo "- Add extension PostGIS"
$SUDO "psql ${DB_NAME} <<EOF
CREATE EXTENSION postgis;
EOF
"
