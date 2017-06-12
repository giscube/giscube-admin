import os
import subprocess
from osgeo import osr, gdal, ogr
from django.contrib.gis.geos import Polygon, MultiPolygon


def get_image_file_info(path):
    """
    Given a path to an image, return
    - width
    - height
    - bounding box
    - number of overviews
    """

    dataset = gdal.Open(path)
    if dataset is None:
        return None

    width = dataset.RasterXSize
    height = dataset.RasterYSize
    gt = dataset.GetGeoTransform()
    extent = GetExtent(gt, width, height)
    bbox = (extent[1][0], extent[1][1], extent[3][0], extent[3][1])

    return {
        'path': path,
        'width': width,
        'height': height,
        'bbox': bbox,
    }


def get_image_dir_info(path, projection=4326):
    supported_extensions = ('.tif', '.jpg', '.png')
    vrtfile = 'all.vrt'
    valid_files = []
    for f in os.listdir(path):
        filename, file_extension = os.path.splitext(f)
        if file_extension.lower() in supported_extensions:
            info = get_image_file_info(os.path.join(path, f))
            valid_files.append(info)

    os.chdir(path)
    args = ['gdalbuildvrt', '-addalpha', vrtfile]
    for info in valid_files:
        args.append(info['path'])
    result = subprocess.call(args)

    return get_image_file_info(os.path.join(path, vrtfile))


def get_image_dir_info_tileindex(path, projection=4326):
    supported_extensions = ('.tif', '.jpg', '.png')
    valid_files = []
    for f in os.listdir(path):
        filename, file_extension = os.path.splitext(f)
        if file_extension.lower() in supported_extensions:
            info = get_image_file_info(os.path.join(path, f))
            valid_files.append(info)

    # generate tileindex with valid files
    data_source, layer = _create_tileindex_layer(path, projection)
    polygons = []
    for info in valid_files:
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetField('location', str(info['path']))
        polygon = Polygon.from_bbox(info['bbox'])
        polygon.srid = projection
        polygons.append(polygon)
        feature.SetGeometry(ogr.CreateGeometryFromWkt(polygon.wkt))
        layer.CreateFeature(feature)
        feature.Destroy()
    data_source.Destroy()

    mp = MultiPolygon(polygons)
    info = {
        'bbox': mp.envelope.extent
    }
    return info


def _create_tileindex_layer(path, projection):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    data_source = driver.Open(path, 1)
    if data_source:
        layer = data_source.GetLayer(0)
        feat = layer.GetNextFeature()
        while feat:
            featId = feat.GetFID()
            layer.DeleteFeature(featId)
            feat = layer.GetNextFeature()
    else:
        data_source = driver.CreateDataSource(path)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(projection)
        layer = data_source.CreateLayer('tileindex', srs, ogr.wkbPolygon)
        field_name = ogr.FieldDefn('location', ogr.OFTString)
        field_name.SetWidth(255)
        layer.CreateField(field_name)

    return data_source, layer


def gdal_build_overviews(path):
    dataset = gdal.Open(path)
    driver = dataset.GetDriver()
    if path.endswith('.tif'):
        gdal.SetConfigOption('COMPRESS_OVERVIEW', 'JPEG')
        gdal.SetConfigOption('PHOTOMETRIC_OVERVIEW', 'YCBCR')
        gdal.SetConfigOption('INTERLEAVE_OVERVIEW', 'PIXEL')
        gdal.SetConfigOption('JPEG_QUALITY_OVERVIEW', '85')

    # check how many levels do we need to build
    levels = []
    width = dataset.RasterXSize
    height = dataset.RasterYSize
    level = 2
    while width > 256 or height > 256:
        levels.append(level)
        level = level * 2
        width = width / 2
        height = height / 2

    dataset.BuildOverviews(resampling='nearest', overviewlist=levels)


# from http://gis.stackexchange.com/questions/57834/how-to-get-raster-corner-coordinates-using-python-gdal-bindings
def GetExtent(gt,cols,rows):
    ''' Return list of corner coordinates from a geotransform

        @type gt:   C{tuple/list}
        @param gt: geotransform
        @type cols:   C{int}
        @param cols: number of columns in the dataset
        @type rows:   C{int}
        @param rows: number of rows in the dataset
        @rtype:    C{[float,...,float]}
        @return:   coordinates of each corner
    '''
    ext=[]
    xarr=[0,cols]
    yarr=[0,rows]

    for px in xarr:
        for py in yarr:
            x=gt[0]+(px*gt[1])+(py*gt[2])
            y=gt[3]+(px*gt[4])+(py*gt[5])
            ext.append([x,y])
        yarr.reverse()
    return ext

def ReprojectCoords(coords,src_srs,tgt_srs):
    ''' Reproject a list of x,y coordinates.

        @type geom:     C{tuple/list}
        @param geom:    List of [[x,y],...[x,y]] coordinates
        @type src_srs:  C{osr.SpatialReference}
        @param src_srs: OSR SpatialReference object
        @type tgt_srs:  C{osr.SpatialReference}
        @param tgt_srs: OSR SpatialReference object
        @rtype:         C{tuple/list}
        @return:        List of transformed [[x,y],...[x,y]] coordinates
    '''
    trans_coords=[]
    transform = osr.CoordinateTransformation( src_srs, tgt_srs)
    for x,y in coords:
        x,y,z = transform.TransformPoint(x,y)
        trans_coords.append([x,y])
    return trans_coords
