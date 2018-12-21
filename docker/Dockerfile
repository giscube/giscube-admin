FROM microdisseny/py-development

RUN apt-get update && \
    apt-get install -y vim && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ADD docker_00.sql /tmp
ADD docker_01.sql /tmp
ADD docker_02.sql /tmp

RUN /etc/init.d/postgresql start && \
    su - postgres -c 'psql' < /tmp/docker_00.sql && \
    su - postgres -c 'psql' < /tmp/docker_01.sql && \
    su - postgres -c 'psql -d sit_example' < /tmp/docker_02.sql

ADD requirements.txt /requirements.txt
RUN pip2 install -r requirements.txt

RUN echo 'user ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
# FIX-ME
# RUN mkdir -p /app
WORKDIR /app


RUN mv /entrypoint.sh /main_entrypoint.sh
ADD entrypoint.sh /entrypoint.sh
RUN chmod -v +x /entrypoint.sh
