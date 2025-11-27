#
#                        BUILD TEMPORARY BUILD-SYSTEM
#
# Downloads all the pip with the given ssh key. Allows to use private repos
#  without the key
#
FROM microdisseny/py3-development:ubuntu-20.04 as build-system

ADD docker/config/known_hosts /root/.ssh/known_hosts

ADD ./requirements*.txt /tmp/

# Download python requirements
ARG EXTRA_REQUIREMENTS=devel
ARG PIP_PACKAGES
ARG APT_PACKAGES

RUN \
  set -e; \
  if [ -n "$APT_PACKAGES_BUILD" ]; then \
    apt-get update && \
    apt -y install $APT_PACKAGES_BUILD; \
  fi; \
  if [ -n "$PIP_PACKAGES" ]; then \
    pip3 install $PIP_PACKAGES; \
  fi;

RUN --mount=type=ssh \
  set -e; \
  pip3 install -U pip; \
  mkdir /pip; \
  if [ -n "$EXTRA_REQUIREMENTS" -a -f "/tmp/requirements-$EXTRA_REQUIREMENTS.txt" ]; then \
    pip3 download -d /pip -r /tmp/requirements.txt -r "/tmp/requirements-$EXTRA_REQUIREMENTS.txt"; \
  else \
    pip3 download -d /pip -r /tmp/requirements.txt; \
  fi;


#
#                            BUILD RUNTIME SYSTEM
#
# The actuall system that will be run
#
FROM microdisseny/py3-development:ubuntu-20.04

# Copy files
RUN mkdir -p /app
RUN mkdir -p /docker
ADD docker/django/entrypoint.sh /docker/
ADD docker/django/bash.sh /docker/
RUN chmod +x /docker/*.sh

# Install python requirements
COPY --from=build-system /pip /pip
ARG PIP_PACKAGES

RUN \
  set -e; \
  if [ -n "$APT_PACKAGES" ]; then \
    apt-get update && \
    apt -y install $APT_PACKAGES; \
  fi; \
  if [ -n "$PIP_PACKAGES" ]; then \
    pip3 install $PIP_PACKAGES; \
  fi;
RUN pip3 install -U pip
RUN pip3 install /pip/*
RUN rm -rf /pip

# Configure run

# Configuración para plugins
ADD docker-custom/plugins/plugins.sh /docker/
ADD app-plugins.env /docker/

# Script para clonar repos y configurar plugins
RUN \
  mkdir -p ~/.ssh && \
  ssh-keyscan bitbucket.org >> ~/.ssh/known_hosts

VOLUME /app/plugins_src
VOLUME /app/plugins_src

ARG SSH_PRIVATE_KEY
ARG SSH_PUBLIC_KEY
RUN \
  set -e; \
  /bin/bash -c /docker/plugins.sh

RUN \
  set -e; \
  /bin/bash -c ls /app/plugins_src

WORKDIR /app
ENTRYPOINT ["/docker/entrypoint.sh"]
CMD ["/bin/bash", "/app/docker-custom/plugins/plugins_links.sh"]
