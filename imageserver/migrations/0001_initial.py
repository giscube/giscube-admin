# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Layer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('title', models.CharField(max_length=100, null=True, blank=True)),
                ('group', models.CharField(max_length=100, null=True, blank=True)),
                ('projection', models.IntegerField(help_text=b'EPSG code')),
                ('extent', django.contrib.gis.db.models.fields.PolygonField(srid=4326, null=True, blank=True)),
                ('mask', models.FileField(null=True, upload_to=b'unique_layer_directory', blank=True)),
                ('image', models.CharField(help_text=b'Image file or folder with tiled images', max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LayerPreview',
            fields=[
                ('layer', models.OneToOneField(primary_key=True, serialize=False, to='imageserver.Layer', on_delete=models.CASCADE)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('service_path', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NamedMask',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('projection', models.IntegerField(help_text=b'EPSG code')),
                ('mask', models.FileField(upload_to=b'unique_mask_directory')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('title', models.CharField(max_length=100, null=True, blank=True)),
                ('projection', models.IntegerField(help_text=b'EPSG code')),
                ('supported_srs', models.CommaSeparatedIntegerField(help_text=b'Comma separated list of supported EPSG codes', max_length=400)),
                ('extent', django.contrib.gis.db.models.fields.PolygonField(srid=4326, null=True, blank=True)),
                ('service_path', models.CharField(max_length=255)),
                ('active', models.BooleanField(default=True)),
                ('visibility', models.CharField(default=b'private', max_length=10, choices=[(b'private', b'Private'), (b'public', b'Public')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ServiceLayer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('layer', models.ForeignKey(to='imageserver.Layer', on_delete=models.CASCADE)),
                ('service', models.ForeignKey(to='imageserver.Service', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='layer',
            name='named_mask',
            field=models.ForeignKey(blank=True, to='imageserver.NamedMask', null=True, on_delete=models.SET_NULL),
            preserve_default=True,
        ),
    ]
