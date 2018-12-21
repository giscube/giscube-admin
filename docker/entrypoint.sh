#!/bin/bash
set -e


if [[ -z "${TEST_DB_ENGINE}" ]]; then
  TEST_DB_ENGINE="sqlite"
else
    if [ "${TEST_DB_ENGINE}" == "postgres" ]
    then
        service postgresql start
    fi
fi

. /main_entrypoint.sh
