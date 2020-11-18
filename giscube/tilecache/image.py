from TileCache.Caches.Test import Test as NoCache
from TileCache.Layers.WMS import WMS


class GiscubeTileCacheWMS(WMS):
    pass


def tile_cache_image(wms_options, buffer, cache_obj=None):
    if cache_obj is None:
        cache_obj = NoCache()
    url = wms_options.get('url')
    layers = wms_options.get('layers')
    bbox = wms_options.get('bbox')
    width = wms_options.get('width', 256)
    height = wms_options.get('height', 256)
    size = list(map(int, [width, height]))
    dpi = wms_options.get('dpi')
    srs = wms_options.get('srs')

    wms = GiscubeTileCacheWMS(layers,
                              url=url,
                              srs=srs,
                              levels=30,
                              spherical_mercator='true',
                              size=size
                              )
    wms.cache = cache_obj
    wms.metaSize = (1, 1)

    # if dpi is specified, adjust buffer
    if dpi:
        ratio = float(dpi) / 91.0
        buffer = [int(x * ratio) for x in buffer]

    wms.metaBuffer = buffer

    tile = wms.getTile(bbox)
    # metatile = wms.getMetaTile(tile)
    # return wms.renderMetaTile(metatile, tile)
    # call renderTile instead of renderMetaTile to use the cache
    wms.metaTile = True
    return wms.render(tile)
