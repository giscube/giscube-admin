import os
from django.conf import settings
from django.contrib.gis.gdal import CoordTransform, SpatialReference


class MapserverLayerWriter(object):
    def write(self, layer, supported_srs):
        a = []

        mask_name = None
        if layer.mask:
            mw = MapserverMaskWriter()
            mask, mask_name = mw.write(layer.name, layer.mask_path, layer.projection)
            a.extend(mask)

        if layer.named_mask:
            mask_name = MapserverMaskWriter.get_mask_name(layer.named_mask.name)

        # LAYER item
        a.append('LAYER')
        a.append('  TYPE RASTER')
        a.append('  NAME "%s"' % layer.name)
        if os.path.isdir(layer.image):
            a.append('  DATA "%s/all.vrt"' % layer.image)
        else:
            a.append('  DATA "%s"' % layer.image)

        # transform layers extent to layer srid
        ct = CoordTransform(SpatialReference('WGS84'),
                            SpatialReference(layer.projection))
        extent = layer.extent.clone()
        extent.transform(ct)

        a.append('  EXTENT %s %s %s %s' % extent.extent)
        # PROJECTION
        a.append('  PROJECTION')
        a.append('    "init=epsg:%s"' % layer.projection)
        a.append('  END')

        srss = supported_srs.split(',')
        srss = [('EPSG:%s' % x.strip()) for x in srss]
        srss = ' '.join(srss)
        # MASK
        if mask_name:
            a.append('  MASK "%s"' % mask_name)
        # METADATA
        a.append('  METADATA')
        a.append('    "wms_title" "%s"' % layer.title)
        a.append('    "wms_srs" "%s"' % srss)
        a.append('    "wms_bbox_extended" "true"')
        a.append('  END')
        # optimization
        a.append('  STATUS OFF')
        # quality options
        a.append('  PROCESSING "RESAMPLE=BILINEAR"')
        # LAYER END
        a.append('END')
        # Force newline at end
        a.append('')
        return '\n'.join(a)


class MapserverMaskWriter(object):
    @staticmethod
    def get_mask_name(layer_name):
        return '%s__mask_layer' % layer_name

    def write(self, name, path, projection):
        a = []
        mask_name = MapserverMaskWriter.get_mask_name(name) 
        # LAYER item for mask
        a.append('LAYER')
        a.append('  TYPE POLYGON')
        a.append('  NAME "%s"' % mask_name)
        a.append('  DATA "%s"' % path)
        # PROJECTION
        a.append('  PROJECTION')
        a.append('    "init=epsg:%s"' % projection)
        a.append('  END')
        a.append('  CLASS')
        a.append('    STYLE')
        a.append('      COLOR 0 0 0')
        a.append('    END')
        a.append('  END')
        # METADATA
        a.append('  METADATA')
        a.append('    "wms_enable_request" "!GetCapabilities"')
        a.append('  END')
        # optimization
        a.append('  STATUS OFF')
        # LAYER END
        a.append('END')
        # Force newline at end
        a.append('')
        return a, mask_name


class MapserverMapWriter(object):
    def write(self, service, layers):
        a = []
        # MAP item
        a.append('MAP')

        a.append('  NAME "%s"' % service.name)
        a.append('  PROJECTION')
        a.append('    "init=epsg:%s"' % service.projection)
        a.append('  END')
        a.append('')

        if service.extent:
            extent = service.extent.clone()
            # transform service extent to desired service srid
            ct = CoordTransform(SpatialReference('WGS84'),
                                SpatialReference(service.projection))
            extent.transform(ct)
            a.append('  EXTENT %s %s %s %s' % extent.extent)
            a.append('')

        srss = service.supported_srs.split(',')
        srss = [('EPSG:%s' % x.strip()) for x in srss]
        srss = ' '.join(srss)
        server = getattr(settings, 'GISCUBE_URL', 'http://localhost')
        a.append('  WEB')
        a.append('    METADATA')
        a.append('      "wms_title" "%s"' % service.title)
        a.append('      "wms_srs" "%s"' % srss)
        a.append('      "wms_enable_request" "GetCapabilities GetMap"')
        a.append('      "wms_onlineresource" "%s/imageserver/services/%s/?"'
                                                    % (server, service.name))
        a.append('      "wms_bbox_extended" "true"')
        a.append('    END')
        a.append('  END')
        a.append('')

        lw = MapserverLayerWriter()
        named_masks = set()
        for layer in layers:
            if layer.named_mask and layer.named_mask not in named_masks:
                mw = MapserverMaskWriter()
                mask, _ = mw.write(layer.named_mask.name, layer.named_mask.mask_path, layer.named_mask.projection)
                a.extend(mask)
                named_masks.add(layer.named_mask)

            a.append(lw.write(layer, service.supported_srs))
            a.append('')

        # MAP END
        a.append('END')
        # Force newline at end
        a.append('')
        return '\n'.join(a)
