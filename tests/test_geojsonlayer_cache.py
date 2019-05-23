import datetime
from unittest import mock

from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone

from layerserver.models import GeoJsonLayer
from layerserver.utils import (GENERATE_GEOJSON_LAYER, GET_DATA_FROM_CACHE, QUEUE_GENERATE_GEOJSON_LAYER,
                               geojsonlayer_check_cache)


def fake_async_geojsonlayer_refresh(*args, **kwargs):
    pass


def fake_geojsonlayer_refresh_layer(*args, **kwargs):
    pass


@override_settings(TIME_ZONE='Europe/Madrid')
class GeoJsonLayerCheckCacheTestCase(TestCase):
    @mock.patch("layerserver.tasks.async_geojsonlayer_refresh.delay", fake_async_geojsonlayer_refresh)
    @mock.patch("layerserver.utils.geojsonlayer_refresh_layer", fake_geojsonlayer_refresh_layer)
    def test_get_from_cache(self):
        layer = GeoJsonLayer()
        layer.url = 'http://localhost'
        layer.generated_on = timezone.localtime() - datetime.timedelta(minutes=10)
        layer.cache_time = 60 * 60  # 1 hour
        layer.save()
        self.assertEqual(GET_DATA_FROM_CACHE, geojsonlayer_check_cache(layer))

    @mock.patch("layerserver.tasks.async_geojsonlayer_refresh.delay", fake_async_geojsonlayer_refresh)
    @mock.patch("layerserver.utils.geojsonlayer_refresh_layer", fake_geojsonlayer_refresh_layer)
    def test_check_async_refresh(self):
        layer = GeoJsonLayer()
        layer.url = 'http://localhost'
        layer.generated_on = timezone.localtime() - datetime.timedelta(hours=5)
        layer.cache_time = 60 * 5  # seconds
        layer.save()
        self.assertEqual(QUEUE_GENERATE_GEOJSON_LAYER, geojsonlayer_check_cache(layer))

    @mock.patch("layerserver.tasks.async_geojsonlayer_refresh.delay", fake_async_geojsonlayer_refresh)
    @mock.patch("layerserver.utils.geojsonlayer_refresh_layer", fake_geojsonlayer_refresh_layer)
    def test_check_refresh(self):
        layer = GeoJsonLayer()
        layer.url = 'http://localhost'
        layer.generated_on = timezone.localtime() - datetime.timedelta(minutes=35)
        layer.cache_time = 30 * 60  # seconds
        layer.max_outdated_time = 5  # seconds
        layer.save()
        self.assertEqual(GENERATE_GEOJSON_LAYER, geojsonlayer_check_cache(layer))
