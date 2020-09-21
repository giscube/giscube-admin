import os

from django.contrib.gis.db import models
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.core.validators import validate_comma_separated_integer_list
from django.utils.translation import gettext as _

from giscube.model_mixins import MetadataModelMixin, ResourceModelMixin
from giscube.models import Category
from giscube.validators import validate_options_json_format
from imageserver.mapserver import MapserverMapWriter
from imageserver.storage import LayerStorage, NamedMaskStorage
from imageserver.utils import extract_zipfile, find_shapefile, unique_layer_directory, unique_service_directory

from .gdal_utils import get_image_dir_info, get_image_file_info


SERVICE_VISIBILITY_CHOICES = [
    ('private', _('Private')),
    ('public', _('Public')),
]

layerStorage = LayerStorage()
namedMaskStorage = NamedMaskStorage()


class Service(models.Model):
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='imageserver_services')
    name = models.CharField(_('name'), max_length=50, unique=True)
    title = models.CharField(_('title'), max_length=100, null=True, blank=True)
    description = models.TextField(_('description'), null=True, blank=True)
    keywords = models.CharField(_('keywords'), max_length=200, null=True, blank=True)
    projection = models.IntegerField(_('projection'), help_text=_('EPSG code'))
    supported_srs = models.CharField(
        _('supported srs'), max_length=400, help_text=_('Comma separated list of supported EPSG codes'),
        validators=[validate_comma_separated_integer_list])
    extent = models.PolygonField(_('name'), null=True, blank=True)
    service_path = models.CharField(_('extent'), max_length=255)
    active = models.BooleanField(_('active'), default=True, help_text='Enable/disable usage')
    visibility = models.CharField(_('visibility'), max_length=10, default='private',
                                  help_text=_('visibility=\'Private\' restricts usage to authenticated users'),
                                  choices=SERVICE_VISIBILITY_CHOICES)
    visible_on_geoportal = models.BooleanField(_('visible on geoportal'), default=False)
    options = models.TextField(_('options'), null=True, blank=True, help_text=_('json format. Ex: {"maxZoom": 20}'),
                               validators=[validate_options_json_format])
    legend = models.TextField(_('legend'), null=True, blank=True)

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

    @property
    def anonymous_view(self):
        return not (self.visibility == 'private')

    class Meta:
        verbose_name = _('Service')
        verbose_name_plural = _('Services')


class ServiceMetadata(MetadataModelMixin):
    parent = models.OneToOneField(Service, on_delete=models.CASCADE, primary_key=True, related_name='metadata')


class ServiceResource(ResourceModelMixin):
    parent = models.ForeignKey(Service, related_name='resources', on_delete=models.CASCADE)


def get_named_mask_upload_path(obj, filename):
    mask_target = os.path.join(obj.name, filename)
    return mask_target


class NamedMask(models.Model):
    name = models.CharField(_('name'), max_length=100)
    projection = models.IntegerField(_('projection'), help_text=_('EPSG code'))
    mask = models.FileField(_('mask'), upload_to=get_named_mask_upload_path,
                            storage=namedMaskStorage)
    mask_path = models.CharField(_('mask path'), max_length=255, null=True, blank=True)

    # TODO: override save() and check if name has changed -> rename directory
    def save(self, *args, **kwargs):
        super(NamedMask, self).save(*args, **kwargs)
        target_path = extract_zipfile(self.mask.path)
        shape = find_shapefile(target_path)
        self.mask_path = shape
        super(NamedMask, self).save(*args, **kwargs)

    def __str__(self):
        return "%s (%s)" % (self.name, self.projection)

    class Meta:
        verbose_name = _('Mask')
        verbose_name_plural = _('Masks')


def get_mask_upload_path(obj, filename):
    mask_dir = os.path.join(obj.layer_path, 'mask')
    mask_target = os.path.join(mask_dir, filename)
    return mask_target


class Layer(models.Model):
    name = models.CharField(_('name'), max_length=50, unique=True)
    title = models.CharField(_('title'), max_length=100, null=True, blank=True)
    group = models.CharField(_('group'), max_length=100, null=True, blank=True)
    projection = models.IntegerField(_('projection'), help_text='EPSG code')
    extent = models.PolygonField(_('extent'), null=True, blank=True)
    layer_path = models.CharField(_('layer path'), max_length=255)
    named_mask = models.ForeignKey(NamedMask, null=True, blank=True, on_delete=models.SET_NULL)
    mask = models.FileField(
        _('file mask'), upload_to=get_mask_upload_path, storage=layerStorage, null=True, blank=True)
    mask_path = models.CharField(_('name'), max_length=255, null=True, blank=True)
    image = models.CharField(
        _('image'), max_length=255, help_text=_('Image file or folder with tiled images'))

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

    def __str__(self):
        return '%s' % self.title

    class Meta:
        verbose_name = _('Layer')
        verbose_name_plural = _('Layers')


class ServiceLayer(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    layer = models.ForeignKey(
        Layer, related_name="services", on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Service Layer')
        verbose_name_plural = _('Services Layers')


class LayerPreview(models.Model):
    layer = models.OneToOneField(
        Layer, primary_key=True, on_delete=models.CASCADE)
    name = models.CharField('name', max_length=50, unique=True)
    service_path = models.CharField('service path', max_length=255)

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

    class Meta:
        verbose_name = _('Layer Preview')
        verbose_name_plural = _('Layer Previews')
