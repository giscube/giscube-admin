# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-05-29 11:11


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('qgisserver', '0009_auto_20180425_1526'),
        ('layerserver', '0008_auto_20180529_1051'),
    ]

    operations = [
        migrations.AlterField(
            model_name='databaselayerreference',
            name='layer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='references', to='layerserver.DataBaseLayer'),
        ),
        migrations.AlterUniqueTogether(
            name='databaselayerreference',
            unique_together=set([('layer', 'service')]),
        ),
    ]
