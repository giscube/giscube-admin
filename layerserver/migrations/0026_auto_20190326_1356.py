# Generated by Django 2.1.7 on 2019-03-26 13:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('layerserver', '0025_auto_20190326_1352'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='databaselayerfield',
            options={'ordering': ['layer', 'name'], 'verbose_name': 'Field', 'verbose_name_plural': 'Fields'},
        ),
    ]
