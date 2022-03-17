FROM microdisseny/py3-development:ubuntu-18.04

MAINTAINER MICRODISSENY GISCUBE SL <tech@microdisseny.com>

ADD qgis.list /etc/apt/sources.list.d/

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-key 46B5721DBBD2996A

RUN apt update && apt install -y nginx supervisor uwsgi qgis-server

RUN mkdir -p /docker
ADD uwsgi.ini /docker/
ADD entrypoint.sh /docker/

ENTRYPOINT ["/bin/bash", "/docker/entrypoint.sh"]

CMD ["/usr/bin/uwsgi", "--ini", "/docker/uwsgi.ini"]
