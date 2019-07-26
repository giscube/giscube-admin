# Generated by Django 2.1.9 on 2019-07-19 07:29

from django.db import migrations, models


def update_fill_color(apps, schema_editor):
    filter = {'shapetype': 'marker', 'marker_color__isnull': False}
    filter_childs = {'layer__shapetype': 'marker', 'marker_color__isnull': False}

    Model = apps.get_model('layerserver', 'DataBaseLayer')
    Model.objects.filter(**filter).update(fill_color=models.F('marker_color'))

    Model = apps.get_model('layerserver', 'DataBaseLayerStyleRule')
    Model.objects.filter(**filter_childs).update(fill_color=models.F('marker_color'))

    Model = apps.get_model('layerserver', 'GeoJsonLayer')
    Model.objects.filter(**filter).update(fill_color=models.F('marker_color'))

    Model = apps.get_model('layerserver', 'GeoJsonLayerStyleRule')
    Model.objects.filter(**filter_childs).update(fill_color=models.F('marker_color'))


def update_fill_color_reverse(apps, schema_editor):
    filter = {'shapetype': 'marker', 'fill_color__isnull': False}
    filter_childs = {'layer__shapetype': 'marker', 'fill_color__isnull': False}

    Model = apps.get_model('layerserver', 'DataBaseLayer')
    Model.objects.filter(**filter).update(marker_color=models.F('fill_color'))

    Model = apps.get_model('layerserver', 'DataBaseLayerStyleRule')
    Model.objects.filter(**filter_childs).update(marker_color=models.F('fill_color'))

    Model = apps.get_model('layerserver', 'GeoJsonLayer')
    Model.objects.filter(**filter).update(marker_color=models.F('fill_color'))

    Model = apps.get_model('layerserver', 'GeoJsonLayerStyleRule')
    Model.objects.filter(**filter_childs).update(marker_color=models.F('fill_color'))


def fake_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('layerserver', '0009_geojsonlayer_design_from'),
    ]

    operations = [
        migrations.RunPython(update_fill_color, update_fill_color_reverse),
        migrations.RemoveField(
            model_name='databaselayer',
            name='marker_color',
        ),
        migrations.RemoveField(
            model_name='databaselayerstylerule',
            name='marker_color',
        ),
        migrations.RemoveField(
            model_name='geojsonlayer',
            name='marker_color',
        ),
        migrations.RemoveField(
            model_name='geojsonlayerstylerule',
            name='marker_color',
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='fill_color',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='fill color'),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='stroke_color',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='stroke color'),
        ),
        migrations.AlterField(
            model_name='databaselayerstylerule',
            name='fill_color',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='fill color'),
        ),
        migrations.AlterField(
            model_name='databaselayerstylerule',
            name='stroke_color',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='stroke color'),
        ),
        migrations.AlterField(
            model_name='geojsonlayer',
            name='fill_color',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='fill color'),
        ),
        migrations.AlterField(
            model_name='geojsonlayer',
            name='stroke_color',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='stroke color'),
        ),
        migrations.AlterField(
            model_name='geojsonlayerstylerule',
            name='fill_color',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='fill color'),
        ),
        migrations.AlterField(
            model_name='geojsonlayerstylerule',
            name='stroke_color',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='stroke color'),
        ),
    ]