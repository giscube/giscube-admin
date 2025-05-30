# giscube-admin

Giscube admin Applications:

- imageserver
- qgisserver
- geoportal

# Requirements.txt
ln -s requirements-gdal3.txt requirements.txt
ln -s requirements-gdal2.txt requirements.txt

## Observations

**geoportal.Dataset.active:** enable/disable usage

**geoportal.Dataset.visibility:** visibility='Private' restricts usage to authenticated users

**imageserver.Service.active:** enable/disable usage

**imageserver.Service.visibility:** visibility='Private' restricts usage to authenticated users

**imageserver.Service.visible_on_geoportal**: enable/disable geoportal indexation

**qgisserver.Service.active:** enable/disables usage

**qgisserver.Service.visibility:** visibility='Private' restricts usage to authenticated users

**qgisserver.Service.visible_on_geoportal**: enable/disable geoportal indexation

**layerserver.GeoJsonLayer.active:** enable/disables usage

**qgisserver.Service.visibility:** visibility='Private' restricts usage to authenticated users

**layerserver.GeoJsonLayer.visible_on_geoportal**: enable/disable geoportal indexation

**layerserver.DataBaseLayer.active:** enable/disables usage

**layerserver.DataBaseLayer.visible_on_geoportal**: enable/disable geoportal indexation



## Run with docker-compose

Copy app.env-example to app.env and adjust values as necessary. On *production* environments, make sure to define the proper value for `CSRF_TRUSTED_ORIGINS`.

Update the git submodules:

``` bash
git submodule update --init --recursive
```

Create the giscube docker network:

``` bash
docker network create giscube
```


### (optional) Build the images

Optional because the next step does it by default (default values only)
By default it installs the development requirements (requirements-devel.txt)

docker-compose build

It's also possible to define to not install development requirements:

docker-compose build --build-arg EXTRA_REQUIREMENTS=''

Or another extra requirement like deploy (requirements-deploy.txt):

docker-compose build --build-arg EXTRA_REQUIREMENTS=deploy


### (Re)Build containers and run Django runserver:

docker-compose up

In background:

docker-compose up -d


### Rebuild one service

docker-compose up django


### Start / Stop during development

docker-compose start
docker-compose stop


## Delete images and containers when done

docker-compose down


### Restart and view logs

docker-compose restart && docker-compose logs -f

docker-compose restart django && docker-compose logs -f


### Interactive bash

docker-compose exec django bash.sh


## Django

### Run migrations

docker-compose exec django bash.sh python3 manage.py migrate

### Run createsuperuser

docker-compose exec django bash.sh python3 manage.py createsuperuser

### Run collectstatic

docker-compose exec django bash.sh python3 manage.py collectstatic

### Run tests

docker-compose exec django bash.sh /bin/bash scripts/run_tests.sh

## Database

Automatic script:

docker-compose exec db bash docker/db/db_init.sh

or

docker-compose exec db bash docker/db/db_init.sh giscube.sql


## Catalan dictionary for giscube_search

Automatic script:

docker-compose exec db bash app/docker-custom/postgres/db_catalan_dictionary.sh
