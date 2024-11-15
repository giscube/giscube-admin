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


class LayerRegister(models.Model):
    layer_name = models.CharField(_('layer name'), max_length=255, null=True, blank=True)
    datetime = models.DateTimeField(_('updated date'), null=True, blank=True)
    username = models.CharField(_("username"), max_length=150)

    class Meta:
        verbose_name = _('Layer register')
        verbose_name_plural = _('Layers register')


class ToolRegister(models.Model):
    tool_name = models.CharField(_('tool name'), max_length=255, null=True, blank=True)
    datetime = models.DateTimeField(_('updated date'), null=True, blank=True)
    username = models.CharField(_("username"), max_length=150)

    class Meta:
        verbose_name = _('Tool register')
        verbose_name_plural = _('Tools register')
