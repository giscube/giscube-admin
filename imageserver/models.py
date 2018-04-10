import glob
import os
import shutil
import zipfile

from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.geos import Polygon, MultiPolygon
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.core.validators import validate_comma_separated_integer_list

from imageserver.mapserver import MapserverMapWriter
from imageserver.storage import NamedMaskStorage, LayerStorage
from imageserver.utils import unique_service_directory, unique_layer_directory, extract_zipfile, find_shapefile

from gdal_utils import get_image_file_info, get_image_dir_info

SERVICE_VISIBILITY_CHOICES = [
    ('private', 'Private'),
    ('public', 'Public'),
]

layerStorage = LayerStorage()
namedMaskStorage = NamedMaskStorage()


class Service(models.Model):
    name = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    keywords = models.CharField(max_length=200, null=True, blank=True)
    projection = models.IntegerField(help_text='EPSG code')
    supported_srs = models.CharField(
        max_length=400,
        help_text='Comma separated list of supported EPSG codes',
        validators=[validate_comma_separated_integer_list])
    extent = models.PolygonField(null=True, blank=True)
    service_path = models.CharField(max_length=255)
    active = models.BooleanField(default=True)
    visibility = models.CharField(max_length=10, default='private',
                                  choices=SERVICE_VISIBILITY_CHOICES)
    visible_on_geoportal = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.service_path is None or self.service_path == '':
            self.service_path = unique_service_directory(self)

        extent = None
        if self.servicelayer_set.count() > 0:
            extents = [sl.layer.extent for sl in self.servicelayer_set.all()]
            extent = MultiPolygon(extents)
            extent = Polygon.from_bbox(extent.extent)
        self.extent = extent

        super(Service, self).save(*args, **kwargs)

        # generate map file
        w = MapserverMapWriter()
        layers = [sl.layer for sl in self.servicelayer_set.all()]
        result = w.write(self, layers)
        with open(os.path.join(self.service_path, 'mapfile.map'), 'w') as f:
            f.write(result)

    @property
    def mapfile_path(self):
        return os.path.join(self.service_path, 'mapfile.map')


def get_named_mask_upload_path(obj, filename):
    mask_target = os.path.join(obj.name, filename)
    return mask_target


class NamedMask(models.Model):
    name = models.CharField(max_length=100)
    projection = models.IntegerField(help_text='EPSG code')
    mask = models.FileField(upload_to=get_named_mask_upload_path,
                            storage=namedMaskStorage)
    mask_path = models.CharField(max_length=255, null=True, blank=True)

    # TODO: override save() and check if name has changed -> rename directory
    def save(self, *args, **kwargs):
        super(NamedMask, self).save(*args, **kwargs)
        target_path = extract_zipfile(self.mask.path)
        shape = find_shapefile(target_path)
        self.mask_path = shape
        super(NamedMask, self).save(*args, **kwargs)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.projection)


def get_mask_upload_path(obj, filename):
    mask_dir = os.path.join(obj.layer_path, 'mask')
    mask_target = os.path.join(mask_dir, filename)
    return mask_target


class Layer(models.Model):
    name = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=100, null=True, blank=True)
    group = models.CharField(max_length=100, null=True, blank=True)
    projection = models.IntegerField(help_text='EPSG code')
    extent = models.PolygonField(null=True, blank=True)
    layer_path = models.CharField(max_length=255)
    named_mask = models.ForeignKey(
        NamedMask, null=True, blank=True, on_delete=models.SET_NULL)
    mask = models.FileField(upload_to=get_mask_upload_path,
                            storage=layerStorage,
                            null=True, blank=True)
    mask_path = models.CharField(max_length=255, null=True, blank=True)
    image = models.CharField(max_length=255,
                                 help_text='Image file or folder with'
                                           ' tiled images')

    def save(self, *args, **kwargs):
        if self.layer_path is None or self.layer_path == '':
            self.layer_path = unique_layer_directory(self)

        if os.path.isdir(self.image):
            info = get_image_dir_info(self.image, self.projection)
        else:
            info = get_image_file_info(self.image)
        polygon = Polygon.from_bbox(info['bbox'])
        polygon.srid = self.projection

        ct = CoordTransform(SpatialReference(self.projection),
                            SpatialReference('WGS84'))
        polygon.transform(ct)
        self.extent = polygon

        super(Layer, self).save(*args, **kwargs)

        # mask
        mask_path = None
        if self.mask:
            target_path = extract_zipfile(self.mask.path)
            mask_path = find_shapefile(target_path)
        self.mask_path = mask_path
        super(Layer, self).save()

        # update layer preview info if any
        if hasattr(self, 'layerpreview'):
            self.layerpreview.save()

        # update services using this layer
        for serviceLayer in self.services.all():
            serviceLayer.service.save()

    def __unicode__(self):
        return '%s' % self.title


class ServiceLayer(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    layer = models.ForeignKey(
        Layer, related_name="services", on_delete=models.CASCADE)


class LayerPreview(models.Model):
    layer = models.OneToOneField(
        Layer, primary_key=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, unique=True)
    service_path = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        self.name = self.layer.name
        if self.service_path is None or self.service_path == '':
            self.service_path = unique_service_directory(self)

        self.extent = self.layer.extent

        super(LayerPreview, self).save(*args, **kwargs)

        self.title = self.layer.title
        self.projection = self.layer.projection
        self.supported_srs = ','.join(['3857', str(self.layer.projection)])

        # generate map file
        w = MapserverMapWriter()
        result = w.write(self, [self.layer])
        with open(os.path.join(self.service_path, 'mapfile.map'), 'w') as f:
            f.write(result)

    @property
    def mapfile_path(self):
        return os.path.join(self.service_path, 'mapfile.map')
