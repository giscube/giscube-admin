import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils._os import abspathu

from giscube.storage import OverwriteStorageMixin


class VarStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        super(VarStorage, self).__init__(*args, **kwargs)

        location = settings.VAR_ROOT
        self.base_location = location
        self.location = abspathu(self.base_location)

        base_url = settings.VAR_URL
        if not base_url.endswith('/'):
            base_url += '/'
        self.base_url = base_url


class LayerStorage(OverwriteStorageMixin, VarStorage):
    def __init__(self, *args, **kwargs):
        super(LayerStorage, self).__init__(*args, **kwargs)

        location = os.path.join(self.base_location, 'imageserver', 'layers')
        self.base_location = location
        self.location = abspathu(self.base_location)


class NamedMaskStorage(OverwriteStorageMixin, VarStorage):
    def __init__(self, *args, **kwargs):
        super(NamedMaskStorage, self).__init__(*args, **kwargs)

        location = os.path.join(self.base_location, 'imageserver', 'named_masks')
        self.base_location = location
        self.location = abspathu(self.base_location)
