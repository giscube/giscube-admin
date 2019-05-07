import io
import logging
import pdf2image
from PIL import Image

from django.conf import settings
from django.core.files.base import ContentFile

from giscube.utils import get_cls


logger = logging.getLogger(__name__)


class ThumbnailFileSystemStorageMixin(object):
    ALLOWED_IMAGE_FORMATS = ('PNG')
    EXTENSIONS = {
        'PNG': 'png',
    }
    PNG_SUPPORTED_MODES = ('1', 'L', 'RGB', 'RGBA')

    def __init__(self, *args, **kwargs):
        self.thumbnail_location = kwargs.pop('thumbnail_location', None)
        self.thumbnail_base_url = kwargs.pop('thumbnail_base_url', None)
        self.thumbnail_width = settings.LAYERSERVER_THUMBNAIL_WIDTH
        self.thumbnail_height = settings.LAYERSERVER_THUMBNAIL_HEIGHT
        if self.thumbnail_location is not None:
            self.thumbnail_width = kwargs.pop('thumbnail_width', None) or self.thumbnail_width
            self.thumbnail_height = kwargs.pop('thumbnail_height', None) or self.thumbnail_height
        super().__init__(*args, **kwargs)

    def delete(self, name, *args, **kwargs):
        super(ThumbnailFileSystemStorageMixin, self).delete(name, *args, **kwargs)
        self.delete_thumbnail(name)

    def delete_thumbnail(self, name):
        thumbnail_name = self.get_thumbnail_name(name)
        storage_thumbnail = self.get_thumbnail_storage()
        if storage_thumbnail.exists(thumbnail_name):
            storage_thumbnail.delete(thumbnail_name)

    def get_thumbnail(self, name):
        thumbnail_name = self.get_thumbnail_name(name)
        storage_thumbnail = self.get_thumbnail_storage()
        if storage_thumbnail.exists(thumbnail_name):
            return {
                'path': storage_thumbnail.path(thumbnail_name),
                'url': storage_thumbnail.url(thumbnail_name)
            }

    def get_thumbnail_name(self, file_name):
        # Only png extension is suported
        extension = 'png'
        return '%s.thumbnail.%s' % (file_name, extension)

    def get_thumbnail_storage(self):
        klass = get_cls('LAYERSERVER_THUMBNAIL_STORAGE_CLASS')
        return klass(location=self.thumbnail_location, base_url=self.thumbnail_base_url)

    def save(self, *args, **kwargs):
        file_name = super(ThumbnailFileSystemStorageMixin, self).save(*args, **kwargs)
        if self.thumbnail_location:
            self.save_thumbnail(file_name)
        return file_name

    def save_thumbnail(self, file_name):
        """
        Save the thumbnail into storage
        """
        storage_thumbnail = self.get_thumbnail_storage()
        result = self._save_thumbnail(file_name)
        if result:
            bytes, extension = result
            filename = self.get_thumbnail_name(file_name)
            storage_thumbnail.save(name=filename, content=ContentFile(bytes))

    def _save_thumbnail(self, file_name):
        """
        Generate a thumbnail
        """
        # Only png extension is supported
        im = None
        format = None
        if file_name.endswith('.pdf'):
            file = self.open(file_name)
            images = pdf2image.convert_from_bytes(file.read(), first_page=1, last_page=1)
            if len(images) > 0:
                im = images[0]
                format = 'PNG'
        else:
            try:
                file = self.open(file_name)
                im = Image.open(file)
                # Keep the same format if it's OK for us
                if im.format in self.ALLOWED_IMAGE_FORMATS:
                    format = im.format
                else:
                    # Convert it into PNG
                    if im.mode not in self.PNG_SUPPORTED_MODES:
                        # Force a valid PNG mode (RGB)
                        im = im.convert('RGBA')
                    format = 'PNG'
            except Exception as e:
                logger.warning(e)
                im = None

        if im:
            # generate thumbnail
            size = (self.thumbnail_width, self.thumbnail_height)
            im.thumbnail(size, Image.ANTIALIAS)
            buffer = io.BytesIO()
            im.save(buffer, format=format)

            buffer.seek(0)
            bytes = buffer.read()
            return bytes, 'png'


def get_image_with_thumbnail_storage_class():
    klass = get_cls('LAYERSERVER_FILE_STORAGE_CLASS')
    return type('ThumbnailFileSystemStorage', (ThumbnailFileSystemStorageMixin, klass), {})
