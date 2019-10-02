from django.contrib.gis.db import models


class ImageWithThumbnailField(models.FileField):
    widget_options = None

    def __init__(self, *args, **kwargs):
        self.widget_options = kwargs.pop('widget_options')
        super().__init__(*args, **kwargs)
        self.validators = []
