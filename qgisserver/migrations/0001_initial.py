# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import qgisserver.utils


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('title', models.CharField(max_length=100, null=True, blank=True)),
                ('project', models.FileField(upload_to=qgisserver.utils.unique_service_directory)),
                ('service_path', models.CharField(max_length=255)),
                ('active', models.BooleanField(default=True)),
                ('visibility', models.CharField(default=b'private', max_length=10, choices=[(b'private', b'Private'), (b'public', b'Public')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
