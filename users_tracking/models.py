from django.db import models
from django.utils.translation import gettext as _


class VisorUserTrack(models.Model):
    username = models.CharField(verbose_name=_("username"), max_length=150)
    ip = models.CharField(verbose_name=_("ip"), max_length=20)
    datetime = models.DateTimeField(verbose_name=_("datetime"))

    class Meta:
        verbose_name = _("Visor user track")
        verbose_name_plural = _("Visor user tracks")

    def __str__(self):
        return f'{self.username} - {self.ip} - {self.datetime}'
