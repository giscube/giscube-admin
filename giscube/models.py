from django.db import models
from django.utils.translation import gettext as _


class Category(models.Model):
    name = models.CharField(max_length=50)
    parent = models.ForeignKey('Category', null=True, blank=True)

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def __unicode__(self):
        if self.parent:
            return '%s > %s' % (self.parent.name, self.name)
        else:
            return '%s' % self.name
