#!/usr/bin/env bash

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

if [[ ${ENVIRONMENT_NAME} = "devel" ]]
  then
    echo "Devel environment, proceeding..."
  else
    echo "Not in devel environment :(, exiting"
    exit 1
fi

PSQL="sudo -u postgres psql -c"

# Standard
echo "- Create database ${DB_NAME}"
$PSQL "CREATE DATABASE \"${DB_NAME}\";"
echo "- Create role ${DB_USER}"
$PSQL "CREATE ROLE \"${DB_USER}\" LOGIN;" ${DB_NAME}
echo "- Set role ${DB_USER} password to ${DB_PASSWORD}"
$PSQL "ALTER ROLE \"${DB_USER}\" WITH PASSWORD '${DB_PASSWORD}';" ${DB_NAME}
echo "- Set role ${DB_USER} permissions SUPERUSER CREATEDB"
$PSQL "ALTER ROLE \"${DB_USER}\" SUPERUSER CREATEDB;" ${DB_NAME}

echo "- CREATE SCHEMA ${DB_USER};" ${DB_NAME}
$PSQL "CREATE SCHEMA \"${DB_USER}\" AUTHORIZATION \"${DB_USER}\"; GRANT ALL ON SCHEMA \"${DB_USER}\" TO \"${DB_USER}\";" ${DB_NAME}

# Extra
echo "- Create role admin"
$PSQL "CREATE ROLE admin PASSWORD 'admin' SUPERUSER CREATEDB CREATEROLE INHERIT LOGIN;"

if [ -z "$1" ]
  then
    echo "No database to import"
    exit 0
fi

echo "Import database in $1"
echo "- Drop schema ${DB_USER}"
$PSQL "DROP SCHEMA \"${DB_USER}\" CASCADE;" ${DB_NAME}
echo "- Drop schema topology"
$PSQL "DROP SCHEMA topology CASCADE;" ${DB_NAME}
echo "- Run file $1"
sudo -u postgres psql --set ON_ERROR_STOP=on ${DB_NAME} < $1
