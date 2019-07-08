import os

from django.core.files.storage import FileSystemStorage


class OverwriteStorageMixin(object):
    def get_available_name(self, name, max_length=256):
        """
        Returns a filename that's free on the target storage system, and
        available for new content to be written to.
        """
        if self.exists(name):
            os.remove(os.path.join(self.location, name))
        return name


class OverwriteStorage(OverwriteStorageMixin, FileSystemStorage):
    pass
