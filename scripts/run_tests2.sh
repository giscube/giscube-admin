export ENVIRONMENT_NAME=test

export TEST_DB_NAME=test
# export TEST_DB_USER=giscube-admin
# export TEST_DB_PASSWORD=giscube-admin
export TEST_DB_HOST=db

ARG1=${1:-tests}

python3 -Wall manage.py test $ARG1
