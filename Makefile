LOCAL_USER_ID=$(shell id -u)

build:
	cp requirements.txt docker-test/requirements.txt && docker build -t microdisseny/giscube-admin-test docker-test

test:
	docker run --rm -e LOCAL_USER_ID=${LOCAL_USER_ID} -e TEST_DB_ENGINE=postgres -e ENVIRONMENT_NAME=test -v ${PWD}:/app -ti microdisseny/giscube-admin-test /bin/bash \
	    -c "python3 manage.py $(MAKECMDGOALS)"

shell:
	docker run --rm -e LOCAL_USER_ID=${LOCAL_USER_ID} -e TEST_DB_ENGINE=postgres -e ENVIRONMENT_NAME=test -v ${PWD}:/app -ti microdisseny/giscube-admin-test /bin/bash
