from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext as _


class WFSMixin(models.Model):

    wfs_enabled = models.BooleanField(_('enabled'), default=False)
    wfs_transaction_enabled = models.BooleanField(_('\'Transaction\' requests enabled'), null=False, default=True)

    class Meta:
        abstract = True
