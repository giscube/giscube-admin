# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-12-07 15:10


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layerserver', '0011_auto_20180726_0745'),
    ]

    operations = [
        migrations.AlterField(
            model_name='geojsonlayer',
            name='cache_time',
            field=models.IntegerField(blank=True, help_text='In seconds', null=True),
        ),
    ]
