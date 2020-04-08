FROM microdisseny/py3-development:ubuntu-18.04

MAINTAINER MICRODISSENY GISCUBE SL <tech@microdisseny.com>

ADD dictionaries/dist/*.dict /usr/share/postgresql/10/tsearch_data/
ADD dictionaries/dist/*.affix /usr/share/postgresql/10/tsearch_data/
ADD dictionaries/dist/*.stop /usr/share/postgresql/10/tsearch_data/

RUN mkdir -p /app

WORKDIR /app

ENTRYPOINT []
