import inspect
import os

from django.conf import settings
from django.contrib.gis.db.models import Extent
from django.core.files.base import ContentFile
from django.db.models import F
from django.urls import reverse
from django.utils.functional import cached_property

from giscube.utils.url import remove_app_url, url_slash_join
from giscube.wms_proxy import WMSProxy

from .model_legacy import create_dblayer_model


SUPORTED_SHAPE_TYPES = ['marker', 'circle', 'line', 'polygon']


class MapserverLayer(WMSProxy):
    def build_url(self, request):
        mapserver_server_url = settings.GISCUBE_IMAGE_SERVER_URL
        meta = request.META.get('QUERY_STRING', '?')
        mapfile = "map=%s" % self.service.mapfile.path
        url = "%s?%s&%s" % (mapserver_server_url, meta, mapfile)
        return url

    def get_wms_buffer_enabled(self):
        return self.style_obj.get_shapetype() == 'circle'

    def get_wms_buffer_size(self):
        size = self.style_obj.max_size()
        if not size:
            size = 64
        return '%s,%s' % (size, size)

    def get_service_name(self):
        return self.service.name

    def get_wms_tile_sizes(self):
        return ['256,256', '512,512']

    def wms(self, request):
        if not self.service.mapfile or request.GET.get('debug', '0') == '1':
            self.write()
        return self.get(request)

    def write(self):
        service = self.service
        Layer = create_dblayer_model(service)

        qs = Layer.objects.all().aggregate(Extent(service.geom_field))
        extent = ' '.join(map(str, qs['%s__extent' % service.geom_field]))

        suported_srids = ['4326', '3857']
        if service.srid not in suported_srids:
            suported_srids.append(service.srid)

        wms_url = url_slash_join(
            settings.GISCUBE_URL, remove_app_url(reverse('content-wms', kwargs={'name': service.name})))

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

        geom_type = (Layer._meta.get_field(service.geom_field).geom_type).replace('MULTI', '')
        if geom_type == 'LINESTRING':
            geom_type = 'LINE'

        vars = {
            'extent': extent,
            'srid': service.srid,
            'name': service.name,
            'title': (service.title or service.name).replace("'", "\'"),
            'pk_field': service.pk_field,
            'table_name': service.table,
            'geom_type': geom_type,
            'geom_field': service.geom_field,
            'wms_srs': ' '.join('EPSG:%s' % x for x in suported_srids),
            'wms_onlineresource': '%s?' % wms_url,
            'connection_type': connection_type,
            'connection_str': connection_str,
            'temppath': os.path.join(settings.MEDIA_ROOT, service.service_path, 'tmp'),
            'styles': StyleLayer(self.service).write()
        }

        if not os.path.exists(vars['temppath']):
            os.makedirs(vars['temppath'])

        template = inspect.cleandoc("""
        MAP
            NAME '{name}'
            UNITS METERS
            EXTENT  {extent}

            WEB
              TEMPPATH "{temppath}"
            END

            SYMBOL
              NAME "mark_symbol_circle_filled"
              TYPE ELLIPSE
              FILLED TRUE
                POINTS
                1 1
              END
            END

            PROJECTION
                "init=epsg:{srid}"
            END

            IMAGECOLOR 255 255 255
            IMAGEQUALITY 95
            IMAGETYPE PNG
            SIZE 1200 1200
            MAXSIZE 4096

            WEB
              METADATA
                "wms_title" '{title}'
                "wms_onlineresource" "{wms_onlineresource}"
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
              IMAGEMODE RGBA
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
                PROJECTION
                   "init=epsg:{srid}"
                END
                {styles}
            END
        END
        """.format(**vars))
        service._mapfile_generated = True
        service.mapfile.save(name='wms.map', content=ContentFile(template))

    @cached_property
    def style_obj(self):
        return StyleLayer(self.service)


class StyleLayer(object):
    def __init__(self, layer):
        self.layer = layer

    def add_alpha(self, original_color, alpha):
        if alpha and alpha != 1:
            original_color += hex(round(float(alpha) * 255))[2:]
        return '"%s"' % original_color

    def fill_style(self, style):
        ms_style = ''
        if style['fill_color'] and style['fill_color'] != '':
            ms_style = """
            STYLE
                COLOR {fill_color}
            END
            """.format(fill_color=self.add_alpha(style['fill_color'], style['fill_opacity']))
        return ms_style

    def stroke_style(self, style):
        ms_style = ''
        if style['stroke_color'] and style['stroke_color'] != '':
            if 'stroke_dash_array' in style and style['stroke_dash_array'] and style['stroke_dash_array'] != '':
                ms_style = """
                STYLE
                    OUTLINECOLOR {stroke_color}
                    WIDTH {stroke_width}
                    LINECAP BUTT
                    PATTERN {stroke_dash_array} END
                END
                """.format(stroke_color=self.add_alpha(style['stroke_color'], style['stroke_opacity']),
                           stroke_width=style['stroke_width'],
                           stroke_dash_array=style['stroke_dash_array'])
            else:
                ms_style = """
                STYLE
                    OUTLINECOLOR {stroke_color}
                    WIDTH {stroke_width}
                END
                """.format(stroke_color=self.add_alpha(style['stroke_color'], style['stroke_opacity']),
                           stroke_width=style['stroke_width'])
        return ms_style

    def circle(self, style, name, expression):
        fill_color = ''
        if style['fill_color'] and style['fill_color'] != '':
            fill_color = 'COLOR %s' % self.add_alpha(style['fill_color'], style['fill_opacity'])
        ms_style = """
        CLASS
            NAME "{name}"
            STYLE
                SYMBOL "mark_symbol_circle_filled"
                SIZE {shape_radius}
                OUTLINECOLOR {stroke_color}
                WIDTH {stroke_width}
                {fill_color}
            END
            {expression}
        END
        """.format(
            name=name.replace('"', '\"'),
            shape_radius=style['shape_radius'],
            stroke_color=self.add_alpha(style['stroke_color'], style['stroke_opacity']),
            stroke_width=style['stroke_width'],
            fill_color=fill_color,
            expression=expression)
        return ms_style

    def line(self, style, name, expression):
        style = """
        CLASS
            NAME "{name}"
            {stroke_style}
            {expression}
        END
        """.format(
            name=name.replace('"', '\"'),
            stroke_style=self.stroke_style(style),
            expression=expression)
        return style

    def polygon(self, style, name, expression):
        style = """
        CLASS
            NAME "{name}"
            {fill_style}
            {stroke_style}
            {expression}
        END
        """.format(
            name=name.replace('"', '\"'),
            stroke_style=self.stroke_style(style),
            fill_style=self.fill_style(style),
            expression=expression)
        return style

    def render_style(self, item, name, expression=None):
        shapetype = self.get_shapetype()
        style = {}

        expression = """EXPRESSION %s""" % expression if expression else ''

        if self.layer.shapetype == 'marker' or shapetype == 'marker':
            style['stroke_color'] = item.stroke_color or settings.LAYERSERVER_STYLE_FILL_COLOR
            style['fill_opacity'] = item.fill_opacity or 1
            if item.stroke_color and item.stroke_width:
                style['stroke_width'] = 1
                style['stroke_opacity'] = item.fill_opacity or 1
            if item.fill_color:
                style['fill_color'] = item.fill_color
            style['shape_radius'] = 12
            return self.circle(style, name, expression)

        if self.layer.shapetype == 'circle':
            style['fill_color'] = item.fill_color
            style['fill_opacity'] = item.fill_opacity

            style['stroke_color'] = item.stroke_color
            style['stroke_width'] = item.stroke_width
            style['stroke_opacity'] = item.stroke_opacity
            style['shape_radius'] = item.shape_radius

            if style['fill_color'] is None and style['stroke_color'] is None:
                style['fill_color'] = item.stroke_color or settings.LAYERSERVER_STYLE_FILL_COLOR
                style['stroke_color'] = item.stroke_color or settings.LAYERSERVER_STYLE_STROKE_COLOR
            return self.circle(style, name, expression)

        if self.layer.shapetype == 'line' or shapetype == 'line':
            style = {}
            style['stroke_color'] = item.stroke_color or settings.LAYERSERVER_STYLE_STROKE_COLOR
            style['stroke_width'] = item.stroke_width
            style['stroke_opacity'] = item.stroke_opacity
            style['stroke_dash_array'] = item.stroke_dash_array
            return self.line(style, name, expression)

        if shapetype == 'polygon':
            style = {}
            style['fill_color'] = item.fill_color
            style['fill_opacity'] = item.fill_opacity

            style['stroke_color'] = item.stroke_color
            style['stroke_width'] = item.stroke_width
            style['stroke_opacity'] = item.stroke_opacity
            style['stroke_dash_array'] = item.stroke_dash_array

            if style['fill_color'] is None and style['stroke_color'] is None:
                style['fill_color'] = item.stroke_color or settings.LAYERSERVER_STYLE_FILL_COLOR
                style['stroke_color'] = item.stroke_color or settings.LAYERSERVER_STYLE_STROKE_COLOR
            return self.polygon(style, name, expression)

    def get_shapetype(self):
        Layer = create_dblayer_model(self.layer)
        geom_type = Layer._meta.get_field(self.layer.geom_field).geom_type.lower()
        shapetype = geom_type

        if shapetype.startswith('multi'):
            shapetype = shapetype[len('multi'):]

        if shapetype == 'linestring':
            shapetype = 'line'

        if shapetype == 'point':
            shapetype = 'circle'

        if self.layer.shapetype == 'image':
            shapetype = 'marker'

        return shapetype

    def render_rules(self):
        rules = []
        for x in self.layer.rules.all().order_by(F('order').asc(nulls_last=False)):
            value = x.value
            if self.is_float(value):
                expression = """(([%s] %s %s))""" % (x.field, x.comparator, value)
            else:
                expression = """(('[%s]' %s '%s'))""" % (x.field, x.comparator, value.replace("'", "\'"))
            style = self.render_style(x, str(x), expression)
            if style:
                rules.append(style)
        return rules

    def write(self, request=None):
        styles = []
        styles += self.render_rules()
        style = self.render_style(self.layer, self.layer.title or self.layer.name)
        if style:
            styles.append(style)
        return "\n".join(styles)

    def max_size(self, request=None):
        sizes = []
        if self.layer.shape_radius and self.is_float(self.layer.shape_radius):
            sizes.append(self.layer.shape_radius)
        for x in self.layer.rules.all():
            if x.shape_radius and self.is_float(x.shape_radius):
                sizes.append(x.shape_radius)
        return max(sizes) if len(sizes) > 0 else None

    def is_float(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False
