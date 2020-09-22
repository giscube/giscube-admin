FROM microdisseny/py3-development:ubuntu-18.04

MAINTAINER MICRODISSENY GISCUBE SL <tech@microdisseny.com>

RUN apt-get update && apt install -y nginx

COPY nginx.conf /etc/nginx/nginx.conf
COPY default.conf /etc/nginx/conf.d/

RUN touch /var/run/nginx.pid && \
  chown -R www-data:www-data /var/run/nginx.pid && \
  chown -R www-data:www-data /var/lib/nginx

RUN mkdir -p /docker
COPY entrypoint.sh /docker/
COPY start.sh /docker/

ENTRYPOINT ["/bin/bash", "/docker/entrypoint.sh"]
CMD ["/bin/bash", "/docker/start.sh"]
