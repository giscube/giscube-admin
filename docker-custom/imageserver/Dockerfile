FROM microdisseny/py3-development:ubuntu-18.04

MAINTAINER MICRODISSENY GISCUBE SL <tech@microdisseny.com>

RUN apt-get update && apt install -y uwsgi cgi-mapserver

RUN mkdir -p /docker
ADD uwsgi.ini /docker/
ADD entrypoint.sh /docker/

ENTRYPOINT ["/bin/bash", "/docker/entrypoint.sh"]

CMD ["/usr/bin/uwsgi", "--ini", "/docker/uwsgi.ini"]
