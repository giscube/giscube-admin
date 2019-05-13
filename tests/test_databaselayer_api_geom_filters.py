from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from giscube.models import DBConnection
from layerserver.model_legacy import create_dblayer_model
from layerserver.models import DataBaseLayer
from tests.common import BaseTest


UserModel = get_user_model()


class DataBaseLayerAPIGeomFiltersTestCase(BaseTest):
    def setUp(self):
        super(self.__class__, self).setUp()
        conn = DBConnection()
        conn.alias = 'test'
        conn.engine = settings.DATABASES['default']['ENGINE']
        conn.name = settings.DATABASES['default']['NAME']
        conn.user = settings.DATABASES['default']['USER']
        conn.password = settings.DATABASES['default']['PASSWORD']
        conn.host = settings.DATABASES['default']['HOST']
        conn.port = settings.DATABASES['default']['PORT']
        conn.save()

        layer = DataBaseLayer()
        layer.db_connection = conn
        layer.name = 'tests_location_25831'
        layer.table = 'tests_location_25831'
        layer.srid = 25831
        layer.pk_field = 'code'
        layer.geom_field = 'geometry'
        layer.anonymous_view = True
        layer.anonymous_add = True
        layer.anonymous_update = True
        layer.anonymous_delete = True
        layer.save()
        self.layer = layer

        # X,Y,lng,lat, address
        data = [
            (485984.399179716, 4646678.69635524, 2.8308397, 41.9719769, 'Carrer de Montori, 6, Girona'),
            (486004.280534943, 4646672.62826433, 2.8310798, 41.9719226, 'Carrer de Montori, 12, Girona'),
            (486015.159965428, 4646685.57498505, 2.8312108, 41.9720394, 'Carrer de Montori, 17, Girona'),
            (485981.063816979, 4646697.33357378, 2.830799, 41.9721447, 'Carrer del Castellet, 1, Girona'),
            (486025.905078693, 4646718.69591949, 2.8313397, 41.9723379, 'Carrer del Turó Rodó, 24, Girona'),
            (485976.301483811, 4646685.65164834, 2.8307418, 41.9720394, 'Carrer de Montori, 7, Girona'),
            (486036.873361096, 4646679.99190294, 2.831473, 41.9719895, 'Carrer de Montori, 23, Girona'),
            (485991.335509501, 4646704.60788712, 2.8309228, 41.9722104, 'Carrer de Sant Grau, 3, Girona'),
            (485995.924639975, 4646687.31164811, 2.8309786, 41.9720547, 'Carrer de Montori, 9, Girona'),
            (485971.231262542, 4646664.92148798, 2.8306811, 41.9718526, 'Carrer de Montori, 2, Girona'),
            (485997.86065962, 4646673.30709788, 2.8310023, 41.9719286, 'Carrer de Montori, 10, Girona'),
            (485991.234154363, 4646674.24171126, 2.8309223, 41.9719369, 'Carrer de Montori, 8, Girona'),
            (486038.970629009, 4646714.22905804, 2.8314975, 41.9722979, 'Carrer del Turó Rodó, 27, Girona'),
            (486029.087115901, 4646714.71482487, 2.8313782, 41.9723021, 'Carrer del Turó Rodó, 29, Girona'),
            (486009.346425706, 4646699.62048077, 2.8311403, 41.9721658, 'Carrer de Montori, 13, Girona'),
            (486032.850809002, 4646682.10936383, 2.8314244, 41.9720085, 'Carrer de Montori, 21, Girona'),
            (486009.503670912, 4646720.54909947, 2.8311417, 41.9723543, 'Carrer de Sant Grau, 7, Girona'),
            (485997.896958484, 4646700.10937757, 2.8310021, 41.97217, 'Carrer de Sant Grau, 4, Girona'),
            (486011.821936575, 4646698.69406302, 2.8311702, 41.9721575, 'Carrer de Montori, 11, Girona'),
            (486023.688015233, 4646682.56041124, 2.8313138, 41.9720124, 'Carrer de Montori, 19, Girona'),
            (486003.516233289, 4646684.19897165, 2.8310703, 41.9720268, 'Carrer de Montori, 15, Girona'),
            (485969.753316113, 4646680.10204534, 2.8306629, 41.9719893, 'Carrer de Montori, 5, Girona'),
            (485976.833113544, 4646673.75941402, 2.8307485, 41.9719323, 'Carrer de Montori, 4, Girona'),
            (485981.073650482, 4646714.89831056, 2.8307987, 41.9723029, 'Carrer del Castellet, 4, Girona'),
            (485984.756663944, 4646704.48763906, 2.8308434, 41.9722092, 'Carrer del Castellet, 2, Girona'),
            (485995.585985817, 4646708.84080015, 2.830974, 41.9722486, 'Carrer de Sant Grau, 5, Girona'),
            (486000.922999553, 4646713.66002545, 2.8310383, 41.9722921, 'Carrer de Sant Grau, 5A, Girona'),
            (486013.232808288, 4646666.24866927, 2.831188, 41.9718653, 'Carrer de Montori, 14, Girona'),
            (485975.306531153, 4646710.45744782, 2.8307292, 41.9722628, 'Carrer del Castellet, 3, Girona'),
        ]

        self.locations = []
        Location = create_dblayer_model(layer)
        self.Location = Location

        for i, item in enumerate(data):
            location = Location()
            location.code = 'B%s' % i
            location.address = item[4]
            location.geometry = 'POINT(%s %s)' % (item[0], item[1])
            location.save()
            self.locations.append(location)

    def test_layer_intersects(self):
        url = reverse('content-list', kwargs={'name': self.layer.name})
        url = '%s?intersects=%s' % (url, 'POLYGON ((2.83090277982049 41.9721696144475,2.8308896918335 '
                                    '41.9722379628241,2.83100457527492 41.9723121280837,2.83113254670334 '
                                    '41.9723892017849,2.83116890222278 41.9723470293824,2.83090277982049 '
                                    '41.9721696144475))')
        response = self.client.get(url)
        self.assertEqual(len(response.json()['features']), 4)

    def test_layer_bbox(self):
        url = reverse('content-list', kwargs={'name': self.layer.name})
        url = '%s?in_bbox=%s' % (url, '2.8309,41.9722,2.831,41.9733')
        response = self.client.get(url)
        self.assertEqual(len(response.json()['features']), 2)
