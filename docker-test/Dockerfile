FROM microdisseny/py3-development:ubuntu-18.04

ENV CPLUS_INCLUDE_PATH "/usr/include/gdal"
ENV C_INCLUDE_PATH "/usr/include/gdal"

ADD requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt

WORKDIR /app
