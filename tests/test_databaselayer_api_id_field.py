from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from giscube.models import DBConnection
from layerserver.model_legacy import create_dblayer_model
from layerserver.models import DataBaseLayer
from tests.common import BaseTest

UserModel = get_user_model()


class DataBaseLayerAPIIDFieldTestCase(BaseTest):
    def setUp(self):
        super(self.__class__, self).setUp()
        conn = DBConnection()
        conn.alias = 'test_connection'
        conn.engine = settings.DATABASES['default']['ENGINE']
        conn.name = settings.DATABASES['default']['NAME']
        conn.user = settings.DATABASES['default']['USER']
        conn.password = settings.DATABASES['default']['PASSWORD']
        conn.host = settings.DATABASES['default']['HOST']
        conn.port = settings.DATABASES['default']['PORT']
        conn.save()

        layer = DataBaseLayer()
        layer.db_connection = conn
        layer.slug = 'tests_location'
        layer.name = 'tests_location'
        layer.table = 'tests_location'
        layer.pk_field = 'code'
        layer.geom_field = 'geometry'
        layer.anonymous_view = True
        layer.anonymous_add = True
        layer.anonymous_update = True
        layer.anonymous_delete = True
        layer.save()
        self.layer = layer

        self.locations = []
        Location = create_dblayer_model(layer)
        self.Location = Location
        for i in range(0, 12):
            location = Location()
            location.code = 'C%s' % str(i).zfill(3)
            location.address = 'C/ Jaume %s, Girona' % i
            location.geometry = 'POINT(0 %s)' % i
            location.save()
            self.locations.append(location)

    def test_id_field_in_properties(self):
        field = self.layer.fields.filter(name='code').first()
        field.enabled = True
        field.save()
        url = reverse('layer-detail', kwargs={'slug': self.layer.slug})
        response = self.client.get(url)
        result = response.json()
        fields = {}
        for field in result['fields']:
            fields[field['name']] = field
        self.assertTrue('code' in fields)

        url = reverse('content-list', kwargs={'layer_slug': self.layer.slug})
        response = self.client.get(url)
        data = response.json()['features'][0]
        self.assertTrue('code' in data['properties'])

    def test_id_field_not_in_properties(self):
        field = self.layer.fields.filter(name='code').first()
        field.enabled = False
        field.save()
        url = reverse('layer-detail', kwargs={'slug': self.layer.slug})
        response = self.client.get(url)
        result = response.json()
        fields = {}
        for field in result['fields']:
            fields[field['name']] = field
        self.assertFalse('code' in fields)

        url = reverse('content-list', kwargs={'layer_slug': self.layer.slug})
        response = self.client.get(url)
        data = response.json()['features'][0]
        self.assertFalse('code' in data['properties'])
