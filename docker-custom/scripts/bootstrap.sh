docker-compose exec db /app/docker/postgres/db_init.sh
docker-compose exec db /app/docker/postgres/db_init_giscube_data.sh

docker-compose exec django python3 manage.py migrate
docker-compose exec django python3 manage.py shell -c "from django.contrib.auth.models import User;User.objects.create_superuser('admin', 'tech@microdisseny.com', 'admin')"
