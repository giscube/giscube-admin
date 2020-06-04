# Generated by Django 2.2.11 on 2020-06-03 06:03

from django.db import migrations, models

def set_interactive(apps, schema_editor):
    DataBaseLayer = apps.get_model('layerserver', 'DataBaseLayer')
    for x in DataBaseLayer.objects.all():
        x.interactive = False if not x.popup else True
        x.save()

    GeoJsonLayer = apps.get_model('layerserver', 'GeoJsonLayer')
    for x in GeoJsonLayer.objects.all():
        x.interactive = False if not x.popup else True
        x.save()

class Migration(migrations.Migration):

    dependencies = [
        ('layerserver', '0022_auto_20200506_0855'),
    ]

    operations = [
        migrations.AddField(
            model_name='databaselayer',
            name='interactive',
            field=models.BooleanField(default=True, verbose_name='interactive layer'),
        ),
        migrations.AddField(
            model_name='geojsonlayer',
            name='interactive',
            field=models.BooleanField(default=True, verbose_name='interactive layer'),
        ),
        migrations.RunPython(set_interactive,  migrations.RunPython.noop),
    ]
