FROM microdisseny/py3-development:ubuntu-20.04

MAINTAINER MICRODISSENY GISCUBE SL <tech@microdisseny.com>

ADD qgis.list /etc/apt/sources.list.d/

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-key D155B8E6A419C5BE

RUN apt update && apt install -y nginx supervisor uwsgi qgis-server

RUN mkdir -p /docker
ADD uwsgi.ini /docker/
ADD entrypoint.sh /docker/

ENTRYPOINT ["/bin/bash", "/docker/entrypoint.sh"]

CMD ["/usr/bin/uwsgi", "--ini", "/docker/uwsgi.ini"]
