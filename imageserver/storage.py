from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils._os import abspathu

import logging
import os

logger = logging.getLogger(__name__)


class OverwriteStorageMixin(object):
    def get_available_name(self, name, max_length=256):
        """
        Returns a filename that's free on the target storage system, and
        available for new content to be written to.
        """
        # If the filename already exists, remove it as if it was a true file system
        if self.exists(name):
            logger.info("DELETE existing file (overwrite)", os.path.join(self.location, name))
            os.remove(os.path.join(self.location, name))
        return name


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
