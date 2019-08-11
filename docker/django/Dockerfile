FROM microdisseny/py3-development:ubuntu-18.04

ARG EXTRA_REQUIREMENTS=devel
ENV EXTRA_REQUIREMENTS $EXTRA_REQUIREMENTS

RUN mkdir -p /app
RUN mkdir -p /docker
RUN mkdir /docker_data

ADD requirements*.txt /docker/
ADD docker/django/entrypoint.sh /docker/
ADD docker/django/bash.sh /docker/
RUN chmod +x /docker/*.sh

RUN pip3 install -r /docker/requirements.txt
RUN if [ -n "$EXTRA_REQUIREMENTS" -a -f "/docker/requirements-$EXTRA_REQUIREMENTS.txt" ]; then pip3 install -r "/docker/requirements-$EXTRA_REQUIREMENTS.txt"; fi

RUN pip3 install uwsgi

WORKDIR /app

ENTRYPOINT ["/docker/entrypoint.sh"]
