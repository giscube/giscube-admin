FROM microdisseny/py3-development:ubuntu-18.04

ARG EXTRA_REQUIREMENTS=devel
ENV EXTRA_REQUIREMENTS $EXTRA_REQUIREMENTS

ARG USER_UID
ENV USER_UID $USER_UID
RUN echo "USER_UID: $USER_UID"

ARG DOCKER_USER
ENV DOCKER_USER $DOCKER_USER
RUN echo "DOCKER_USER: $DOCKER_USER"

ENV PATH /usr/local/bin:$PATH

RUN if [ "$DOCKER_USER" != "www-data" ]; then useradd --shell /bin/bash -u $USER_UID -o -c "" -m user || true ; fi
RUN if [ "$DOCKER_USER" != "www-data" ]; then echo "PATH=\$PATH:/home/$DOCKER_USER/.local/bin/" >> "/home/$DOCKER_USER/.bashrc" ; fi

RUN mkdir -p /app
RUN mkdir -p /docker
RUN mkdir /docker_data

ADD requirements*.txt /docker/
ADD docker/django/entrypoint.sh /docker/
ADD docker/django/bash.sh /docker/
RUN chmod +x /docker/*.sh

ADD docker/django/bash.sh /bin/
RUN chmod +x /bin/bash.sh

RUN pip3 install --upgrade pip
RUN pip3 install -r /docker/requirements.txt
RUN if [ -n "$EXTRA_REQUIREMENTS" -a -f "/docker/requirements-$EXTRA_REQUIREMENTS.txt" ]; then pip3 install -r "/docker/requirements-$EXTRA_REQUIREMENTS.txt"; fi

RUN pip3 install uwsgi

WORKDIR /app

ENTRYPOINT ["/docker/entrypoint.sh"]
