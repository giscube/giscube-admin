#!/usr/bin/env bash

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

# Extra
echo "- Create role admin"
$SUDO "psql ${DB_NAME} <<EOF
CREATE ROLE admin PASSWORD 'admin' SUPERUSER CREATEDB CREATEROLE INHERIT LOGIN;
EOF
"

if [ -z "$1" ]
  then
    echo "No database to import"
    exit 0
fi

echo "Import database in $1"
echo "- Drop schema ${DB_USER}"
$SUDO "psql ${DB_NAME} <<EOF
DROP SCHEMA \"${DB_USER}\" CASCADE;
EOF
"

echo "- Drop schema topology"
$SUDO "psql ${DB_NAME} <<EOF
DROP SCHEMA topology CASCADE;
EOF
"

echo "- Run file $1"
su postgres psql --set ON_ERROR_STOP=on ${DB_NAME} < /app/$1
