import json

from django.urls import reverse

from giscube.models import BaseLayer, MapConfig, MapConfigBaseLayer
from tests.common import BaseTest


mapconfig_data = {
    'name': 'Prova',
    'center_lat': '89.999000',
    'center_lng': '179.999000',
    'initial_zoom': 10
}
baselayer_data1 = {
    'name': 'Capa 1',
    'properties': {'prop1': 'val1', 'prop2': 'val2'}
}
baselayer_data2 = {
    'name': 'Capa 2',
    'properties': {'prop1': 'val1', 'prop2': 'val2'}
}
mapconfig_baselayer_data = {}


class APITestCase(BaseTest):
    def setUp(self):
        mapconfig = MapConfig.objects.create(**mapconfig_data)
        baselayer = BaseLayer.objects.create(**baselayer_data1)
        mapconfig_baselayer_data = {
            'map_config': mapconfig,
            'base_layer': baselayer,
            'order': 2
        }
        MapConfigBaseLayer.objects.create(**mapconfig_baselayer_data)
        baselayer = BaseLayer.objects.create(**baselayer_data2)
        mapconfig_baselayer_data = {
            'map_config': mapconfig,
            'base_layer': baselayer,
            'order': 1
        }
        MapConfigBaseLayer.objects.create(**mapconfig_baselayer_data)
        super().setUp()

    def test_api_mapconfig_details(self):
        url = reverse('map_config-detail', args=[mapconfig_data['name']])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode('utf-8'))

        self.assertEqual(isinstance(result, dict), True)
        self.assertEqual('id' in result, True)

        fields = mapconfig_data.keys()
        has_mapconfig_data = [True for field in fields
                              if field in result and result[field] == mapconfig_data[field]]
        valid_data = [True for field in fields]
        self.assertEqual(has_mapconfig_data, valid_data)

        self.assertEqual('baselayers' in result, True)
        self.assertEqual(isinstance(result['baselayers'], list), True)
        self.assertEqual(isinstance(result['baselayers'][0], dict), True)
