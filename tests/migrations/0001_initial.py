# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-12-12 10:32
from __future__ import unicode_literals

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(blank=True, max_length=50, null=True)),
                ('geometry', django.contrib.gis.db.models.fields.PointField(srid=4326)),
            ],
        ),
    ]
