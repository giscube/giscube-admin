cp ~/.ssh/id_rsa docker/django/ssh/
docker-compose build --force-rm --no-cache requirements
rm docker/django/ssh/id_rsa
