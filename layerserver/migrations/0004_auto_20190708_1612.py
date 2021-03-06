# Generated by Django 2.1.9 on 2019-07-10 14:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layerserver', '0003_auto_20190702_1409'),
    ]

    operations = [
        migrations.AddField(
            model_name='databaselayer',
            name='stroke_opacity',
            field=models.CharField(blank=True, default='1', max_length=50, null=True, verbose_name='stroke opacity'),
        ),
        migrations.AddField(
            model_name='databaselayerstylerule',
            name='stroke_opacity',
            field=models.CharField(blank=True, default='1', max_length=50, null=True, verbose_name='stroke opacity'),
        ),
        migrations.AddField(
            model_name='geojsonlayer',
            name='stroke_opacity',
            field=models.CharField(blank=True, default='1', max_length=50, null=True, verbose_name='stroke opacity'),
        ),
        migrations.AddField(
            model_name='geojsonlayerstylerule',
            name='stroke_opacity',
            field=models.CharField(blank=True, default='1', max_length=50, null=True, verbose_name='stroke opacity'),
        )
    ]
