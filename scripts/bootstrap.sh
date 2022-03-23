# Migrations
docker-compose exec django python3 manage.py migrate

# Admin user
docker-compose exec django python3 manage.py shell -c "from django.contrib.auth.models import User;User.objects.create_superuser('admin', 'tech@microdisseny.com', 'admin')"
