# Generated by Django 2.2.11 on 2020-05-06 05:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_to_anonymous_view(apps, schema_editor):
    GeoJsonLayer = apps.get_model('layerserver', 'GeoJsonLayer')
    for layer in GeoJsonLayer.objects.all():
        layer.anonymous_view = layer.visibility == 'public'
        layer.save()


def undo_migrate_to_anonymous_view(apps, schema_editor):
    GeoJsonLayer = apps.get_model('layerserver', 'GeoJsonLayer')
    for layer in GeoJsonLayer.objects.all():
        if layer.anonymous_view:
            layer.visibility == 'public'
        else:
            layer.visibility == 'private'
        layer.save()


class Migration(migrations.Migration):

    dependencies = [
        ('layerserver', '0019_geojsonlayer_permissions'),
    ]
    operations = [
        migrations.RunPython(migrate_to_anonymous_view, undo_migrate_to_anonymous_view),
        migrations.RemoveField(
            model_name='geojsonlayer',
            name='visibility',
        ),
    ]
