from django.db import models
from django.utils.translation import gettext as _

from .utils import resolve_layer


class VisorUserTrack(models.Model):
    username = models.CharField(verbose_name=_("username"), max_length=150)
    ip = models.CharField(verbose_name=_("ip"), max_length=20)
    datetime = models.DateTimeField(verbose_name=_("datetime"))

    class Meta:
        verbose_name = _("Visor user track")
        verbose_name_plural = _("Visor user tracks")

    def __str__(self):
        return f'{self.username} - {self.ip} - {self.datetime}'


PERMISSION_PUBLIC = 'public'
PERMISSION_PRIVATE = 'private'

PERMISSION_CHOICES = (
    (PERMISSION_PUBLIC, _('Public')),
    (PERMISSION_PRIVATE, _('Private')),
)


class LayerRegister(models.Model):
    layer_name = models.CharField(_('layer name'), max_length=255, null=True, blank=True)
    giscube_id = models.CharField(_('Giscube ID'), max_length=10, null=True, blank=True)
    datetime = models.DateTimeField(_('datetime'), null=True, blank=True)
    username = models.CharField(_("username"), max_length=150, null=True, blank=True)
    permission = models.CharField(
        _('permission'), max_length=20, choices=PERMISSION_CHOICES, null=True, blank=True,
        help_text=_('Visibility of the layer when it was registered'))

    class Meta:
        verbose_name = _('Layer register')
        verbose_name_plural = _('Layers register')

    @staticmethod
    def resolve_permission(giscube_id):
        layer = resolve_layer(giscube_id)
        if layer is None:
            return None

        if getattr(layer, 'anonymous_view', False):
            return PERMISSION_PUBLIC

        return PERMISSION_PRIVATE

    def save(self, *args, **kwargs):
        if not self.permission:
            self.permission = self.resolve_permission(self.giscube_id)
        super().save(*args, **kwargs)


class ToolRegister(models.Model):
    tool_name = models.CharField(_('tool name'), max_length=255, null=True, blank=True)
    datetime = models.DateTimeField(_('datetime'), null=True, blank=True)
    username = models.CharField(_("username"), max_length=150, null=True, blank=True)

    class Meta:
        verbose_name = _('Tool register')
        verbose_name_plural = _('Tools register')
