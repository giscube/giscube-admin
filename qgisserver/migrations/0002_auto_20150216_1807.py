# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('qgisserver', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='description',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='service',
            name='keywords',
            field=models.CharField(max_length=100, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='service',
            name='visible_on_geoportal',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
