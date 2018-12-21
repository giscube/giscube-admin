LOCAL_USER_ID=$(shell id -u)

build:
	cp requirements-gdal2.txt docker/requirements.txt && docker build -t microdisseny/giscube-admin docker

test:
	docker run --rm -e LOCAL_USER_ID=${LOCAL_USER_ID} -e TEST_DB_ENGINE=postgres -e ENVIRONMENT_NAME=test -v ${PWD}:/app -ti microdisseny/giscube-admin /bin/bash \
	    -c "python manage.py $(MAKECMDGOALS)"

shell:
	docker run --rm -e LOCAL_USER_ID=${LOCAL_USER_ID} -e TEST_DB_ENGINE=postgres -e ENVIRONMENT_NAME=test -v ${PWD}:/app -ti microdisseny/giscube-admin /bin/bash
