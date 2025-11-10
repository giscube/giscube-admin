from django.db import models
from django.utils.translation import gettext_lazy as _


class WFSMixin(models.Model):

    wfs_enabled = models.BooleanField(_('enabled'), default=False)
    wfs_transaction_enabled = models.BooleanField(_('Transaction requests enabled'), null=False, default=True)

    class Meta:
        abstract = True
