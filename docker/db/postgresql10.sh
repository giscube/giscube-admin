#!/usr/bin/env bash
# adapted from https://github.com/rgielen/postgresql-ubuntu-docker

LANG=C.UTF-8
PG_VERSION=10
PG_PASSWORD=postgres
PG_BASE=/var/lib/postgresql
PG_PASSWORD_FILE=${PG_BASE}/pwfile
PG_DATA=${PG_BASE}/${PG_VERSION}/main
PG_CONFIG_DIR=/etc/postgresql/${PG_VERSION}/main
PG_CONFIG_FILE=${PG_CONFIG_DIR}/postgresql.conf
PG_BINDIR=/usr/lib/postgresql/${PG_VERSION}/bin

PG_PASSWORD=${PG_PASSWORD:-$(pwgen -c -n -1 16)}

if [ ! -d "$PG_DATA" ]; then

  chown postgres:postgres "$PG_BASE"
  chmod 705 "$PG_BASE"

  echo "${PG_PASSWORD}" > ${PG_PASSWORD_FILE}
  chown postgres:postgres "$PG_PASSWORD_FILE"
  chmod 600 ${PG_PASSWORD_FILE}

  sudo -u postgres -E bash -c "${PG_BINDIR}/initdb --pgdata=${PG_DATA} --pwfile=${PG_PASSWORD_FILE} \
    --username=postgres --encoding=UTF8 --auth=trust"

  echo "*************************************************************************"
  echo " PostgreSQL password is ${PG_PASSWORD}"
  echo "*************************************************************************"

  unset PG_PASSWORD
fi

mkdir -p /var/run/postgresql/$PG_VERSION-main.pg_stat_tmp
chown -R postgres:postgres /var/run/postgresql
chmod g+s /var/run/postgresql

echo "# Configuration from postgresql10.sh" >> $PG_CONFIG_DIR/pg_hba.conf
echo "" >> $PG_CONFIG_DIR/pg_hba.conf
echo "host all  all    0.0.0.0/0  md5" >> $PG_CONFIG_DIR/pg_hba.conf
echo "host all  all    ::/0  md5" >> $PG_CONFIG_DIR/pg_hba.conf
echo "listen_addresses='*'" >> $PG_CONFIG_FILE

exec su -c "${PG_BINDIR}/postgres -D ${PG_DATA} -c config_file=${PG_CONFIG_FILE}" postgres
