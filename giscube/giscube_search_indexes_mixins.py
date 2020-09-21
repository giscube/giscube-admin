class ResourcesIndexMixin:
    def prepare_children(self, obj):
        children = []
        for r in obj.resources.all():
            children.append({
                'title': r.title or r.name,
                'group': False,
                'type': r.type,
                'url': r.url,
                'layers': r.layers,
                'projection': r.projection,
                'giscube': {'getfeatureinfo_support': r.getfeatureinfo_support, 'single_image': r.single_image}
            })
        return children
