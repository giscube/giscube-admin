# Generated by Django 2.2.13 on 2020-08-24 09:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layerserver', '0024_auto_20200604_0758'),
    ]

    operations = [
        migrations.AlterField(
            model_name='databaselayermetadata',
            name='bbox',
            field=models.CharField(blank=True, help_text='The format is: xmin,ymin,xmin,xmax. BBOX coordinates must be in EPSG:4326', max_length=255, null=True, verbose_name='BBOX'),
        ),
        migrations.AlterField(
            model_name='geojsonlayermetadata',
            name='bbox',
            field=models.CharField(blank=True, help_text='The format is: xmin,ymin,xmin,xmax. BBOX coordinates must be in EPSG:4326', max_length=255, null=True, verbose_name='BBOX'),
        ),
    ]
