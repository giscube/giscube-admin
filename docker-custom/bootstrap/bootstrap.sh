# django db service
docker-compose exec db /app/docker/postgres/db_init.sh
docker-compose exec db /app/docker/postgres/db_init_giscube_data.sh

## copy catalan dictionary to db service
docker-compose exec db bash /app/docker-custom/postgres/db_catalan_dictionary.sh

## Install catalan dictionary to giscube database
docker-compose exec db bash -c 'PGPASSWORD="${DB_PASSWORD}" psql -hlocalhost -U${DB_USER} --set ON_ERROR_STOP=on ${DB_NAME} < /app/docker-custom/postgres/dictionaries/catalan.sql'

## django app
docker-compose exec django python3 manage.py migrate

### Create superuser
docker-compose exec django python3 manage.py shell -c "from django.contrib.auth.models import User;User.objects.create_superuser('admin', 'tech@microdisseny.com', 'admin')"

### Add data
docker-compose exec django bash -c 'python3 manage.py shell < /app/docker-custom/bootstrap/scripts/dbconnection.py'
docker-compose exec django bash -c 'python3 manage.py shell < /app/docker-custom/bootstrap/scripts/categories.py'
docker-compose exec db su postgres -c 'psql giscube_data < /app/docker-custom/bootstrap/scripts/sql/bicis.sql'




docker-compose exec -T django bash <<EOF | grep 'b' | tee b.txt
foo
bar
baz
EOF
### Add database layer

### Add geojsonlayer

### Add qgisserver layer

### Add slave server


# django-slave db service
docker-compose exec db /app/docker/postgres/db_init_giscube_slave.sh

## Install catalan dictionary to giscube_slave database
docker-compose exec db bash -c 'PGPASSWORD="${DB_PASSWORD}_slave" psql -hlocalhost -U${DB_USER}_slave --set ON_ERROR_STOP=on ${DB_NAME}_slave < /app/docker-custom/postgres/dictionaries/catalan.sql'

## django-slave app
docker-compose exec django_slave python3 manage.py migrate
docker-compose exec django_slave python3 manage.py shell -c "from django.contrib.auth.models import User;User.objects.create_superuser('admin', 'tech@microdisseny.com', 'admin')"
