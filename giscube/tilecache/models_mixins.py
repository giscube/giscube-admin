from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext as _


class TileCacheModelMixin(models.Model):

    tilecache_enabled = models.BooleanField(_('enabled'), default=False)
    tilecache_bbox = models.CharField(
        _('BBOX'), max_length=255, blank=True, null=True,
        help_text='The format is: xmin,ymin,xmin,xmax. BBOX coordinates must be in EPSG:4326'
    )
    tilecache_minzoom_level = models.SmallIntegerField(
        _('minimum zoom level'),
        blank=False,
        null=False,
        default=4,
        validators=[MaxValueValidator(24), MinValueValidator(0)]
    )
    tilecache_maxzoom_level = models.SmallIntegerField(
        _('maximum zoom level'),
        blank=False,
        null=False,
        default=22,
        validators=[MaxValueValidator(30), MinValueValidator(0)]
    )
    tilecache_expiration_time = models.IntegerField(_('cache expiration time'), help_text=_('Time in seconds'), default=604800)
    tilecache_minZoom_level_chached =models.SmallIntegerField(
        _('min zoom level cached'),
        blank=False,
        null=False,
        default=4,
        validators=[MinValueValidator(0)]
    )
    tilecache_maxZoom_level_chached =models.SmallIntegerField(
        _('max zoom level cached'),
        blank=False,
        null=False,
        default=22,
        validators=[MinValueValidator(0)]
    )


    class Meta:
        abstract = True
