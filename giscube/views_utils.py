from django.shortcuts import render


def web_map_view(request, extra_context):
    """
    Context requires:
    layers:
        {
            name
            url
            type: tile | wms
            layers
        }
    bbox
    base_layer as LEAFLET_CONFIG.TILES
    title
    """

    context = {
        'LEAFLET_CONFIG': {'TILES': 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'}
    }
    context.update(extra_context)
    return render(request, 'admin/giscube/web_map.html', context)
