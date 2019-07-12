import inspect
import time
import urllib.parse

import requests
from requests.exceptions import ConnectionError

from django.conf import settings
from django.contrib.gis.db.models import Extent
from django.core.cache import caches
from django.core.files.base import ContentFile
from django.db.models import F
from django.http import HttpResponse
from django.template import loader
from django.urls import reverse

from giscube.utils.url import remove_app_url, url_slash_join

from .model_legacy import create_dblayer_model


SUPORTED_SHAPE_TYPES = ['circle', 'line', 'polygon']


class MapserverLayer(object):
    def __init__(self, layer):
        self.layer = layer

    def wms(self, request):
        cache = caches['mapserver']
        mapserver_key = 'mapserver_%s' % self.layer.name
        if not self.layer.mapfile or request.GET.get('debug', '0') == '1' or cache.get(mapserver_key) is None:
            self.write()
            cache.set(mapserver_key, '1', 25)

        mapserver_server_url = settings.GISCUBE_IMAGE_SERVER_URL
        meta = request.META.get('QUERY_STRING', '?')
        mapfile = "map=%s" % self.layer.mapfile.path
        sld_body = 'sld_body=%s' % urllib.parse.quote(SLDLayer(self.layer).sld().rstrip('\n\r'))
        url = "%s?%s&%s&%s" % (mapserver_server_url, meta, mapfile, sld_body)
        retrying = False
        response = None
        for retry in range(5):
            try:
                r = requests.get(url)
                content_type = r.headers['content-type']
                if content_type == 'text/xml' and \
                        'ServiceException' in r.content:
                    print('===================================================')
                    print(r.content)

                response = HttpResponse(r.content, content_type=content_type)
                response.status_code = r.status_code
                break
            except ConnectionError as e:
                print(e)

                if retrying:
                    # calm down
                    print('retry number %s' % retry)
                    time.sleep(1)
                else:
                    retrying = True

        if not response:
            response = HttpResponse('Unable to contact server')
            response.status_code = 500

        return response

    def write(self):
        service = self.layer
        Layer = create_dblayer_model(service)

        qs = Layer.objects.all().aggregate(Extent(service.geom_field))
        extent = ' '.join(map(str, qs['%s__extent' % service.geom_field]))

        suported_srids = ['4326', '3857']
        if service.srid not in suported_srids:
            suported_srids.append(service.srid)

        wms_url = url_slash_join(
            settings.GISCUBE_URL, remove_app_url(reverse('content-wms', kwargs={'name': self.layer.name})))

        connection_type = 'POSTGIS'
        vars = {
            'db_hostname': service.db_connection.host or 'localhost',
            'db_dbname': service.db_connection.name,
            'db_port': service.db_connection.port or '5432',
            'db_user': service.db_connection.user,
            'db_password': service.db_connection.password
        }
        connection_str = ("host={db_hostname} port={db_port} dbname='{db_dbname}' user='{db_user}'"
                          " password='{db_password}'").format(**vars)

        vars = {
            'extent': extent,
            'srid': service.srid,
            'name': service.name,
            'title': (service.title or service.name).replace("'", "\'"),
            'pk_field': service.pk_field,
            'table_name': service.table,
            'geom_type': (Layer._meta.get_field(service.geom_field).geom_type).replace('MULTI', ''),
            'geom_field': service.geom_field,
            'wms_srs': ' '.join('EPSG:%s' % x for x in suported_srids),
            'wms_onlineresource': '%s?' % wms_url,
            'connection_type': connection_type,
            'connection_str': connection_str
        }

        template = inspect.cleandoc("""
        MAP
            NAME '{name}'
            UNITS METERS
            EXTENT  {extent}

            WEB
              TEMPPATH "/tmp/"
            END

            PROJECTION
                "init=epsg:{srid}"
            END

            IMAGECOLOR 255 255 255
            IMAGEQUALITY 95
            IMAGETYPE PNG
            #RESOLUTION 96
            SIZE 1200 1200
            MAXSIZE 4096

            WEB
              METADATA
                "wms_title" '{title}'
                "wms_onlineresource" "{wms_onlineresource}"
                "wms_enable_request" "*"
                "wms_srs" "{wms_srs}"
                "wms_feature_info_mime_type" "application/vnd.ogc.gml"
                "wms_enable_request" "GetCapabilities GetMap GetFeatureInfo GetLegendGraphic"
                "wfs_enable_request" "!*"
                "sos_enable_request" "!*"
                "wcs_enable_request" "!*"
              END
            END

            # https://mapserver.org/mapfile/outputformat.html
            OUTPUTFORMAT
              NAME "png"
              DRIVER AGG/PNG
              MIMETYPE "image/png"
              IMAGEMODE RGB
              EXTENSION "png"
              FORMATOPTION "GAMMA=0.75"
              TRANSPARENT ON
            END
            OUTPUTFORMAT
              NAME "jpeg"
              DRIVER AGG/JPEG
              MIMETYPE "image/jpeg"
              IMAGEMODE RGB
              EXTENSION "jpg"
              FORMATOPTION "GAMMA=0.75"
            END
            OUTPUTFORMAT
              NAME "myUTFGrid"
              DRIVER UTFGRID
              FORMATOPTION "LABELS=true"
              FORMATOPTION "UTFRESOLUTION=4"
              FORMATOPTION "DUPLICATES=false"
            END
            LAYER
                NAME '{name}'
                STATUS ON
                TYPE {geom_type}
                CONNECTIONTYPE {connection_type}
                CONNECTION "{connection_str}"
                DATA '{geom_field} from {table_name} using unique {pk_field} using srid={srid}'
                METADATA
                    "wms_name" '{name}'
                    "wms_title" '{title}'
                    "wms_abstract" "-"
                    "gml_include_items" "none"
                    "wms_format" "image/png"
                    "wms_formatlist"  "image/png, image/jpeg"
                END
            END
        END
        """.format(**vars))
        service.mapfile.save(name='wms.map', content=ContentFile(template))


class SLDLayer(object):
    COMPARATOR_CHOICES = {
        '=': 'PropertyIsEqualTo',
        '!=': 'PropertyIsNotEqualTo',
        '>': 'PropertyIsGreaterThan',
        '>=': 'PropertyIsGreaterThanOrEqualTo',
        '<': 'PropertyIsLessThan',
        '<=': 'PropertyIsLessThanOrEqualTo'
    }

    def __init__(self, layer):
        self.layer = layer

    def render_style(self, item, shapetype):
        style = {}

        if self.layer.shapetype == 'circle':
            style['fill_color'] = item.fill_color
            style['fill_opacity'] = item.fill_opacity

            style['stroke_color'] = item.stroke_color
            style['stroke_width'] = item.stroke_width
            style['shape_radius'] = item.shape_radius

        if shapetype == 'linestring':
            style['stroke_color'] = item.stroke_color
            style['stroke_width'] = item.stroke_width
            style['stroke_opacity'] = item.stroke_opacity
            style['stroke_dash_array'] = item.stroke_dash_array

        if shapetype == 'polygon':
            style['fill_color'] = item.fill_color
            style['fill_opacity'] = item.fill_opacity

            style['stroke_color'] = item.stroke_color
            style['stroke_width'] = item.stroke_width
            style['stroke_opacity'] = item.stroke_opacity
            style['stroke_dash_array'] = item.stroke_dash_array

        return style

    def render_rules(self, shapetype):
        rules = []
        for x in self.layer.rules.all().order_by(F('order').asc(nulls_last=False)):
            r = {}
            filter = {}
            filter['comparator'] = self.COMPARATOR_CHOICES[x.comparator]
            filter['field'] = x.field
            filter['value'] = x.value
            r['title'] = str(x)
            r['filter'] = filter
            r['style'] = self.render_style(x, shapetype)
            rules.append(r)
        return rules

    def sld(self, request=None):
        Layer = create_dblayer_model(self.layer)
        geom_type = Layer._meta.get_field(self.layer.geom_field).geom_type.lower().replace('multy', '')

        shapetype = geom_type.replace('multi', '')

        if geom_type == 'point' and self.layer.shapetype == 'circle':
            shapetype = 'circle'

        if geom_type == 'linestring':
            shapetype = 'linestring'

        if geom_type == 'polygon':
            shapetype = 'polygon'

        if self.layer.shapetype == 'image':
            shapetype = 'image'

        tpl = loader.get_template('mapserver/sld/%s.xml' % shapetype)

        context = {}
        context['name'] = self.layer.name
        title = self.layer.title or self.layer.name
        context['title'] = title
        context['rules'] = [{'style': self.render_style(self.layer, shapetype), 'title': title}]
        context['rules'] += self.render_rules(shapetype)

        return tpl.render(context)
