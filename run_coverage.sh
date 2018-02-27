export ENVIRONMENT_NAME=test
coverage run \
  --omit='manage.py','*migrations*','giscube/wsgi.py','giscube/settings-test.py' \
  --source=. manage.py test tests \
  && coverage report -m --skip-covered
