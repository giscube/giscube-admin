# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-07-26 07:45


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layerserver', '0010_auto_20180601_0710'),
    ]

    operations = [
        migrations.AlterField(
            model_name='databaselayer',
            name='geom_field',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
