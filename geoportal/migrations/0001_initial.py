# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('title', models.CharField(max_length=100, null=True, blank=True)),
                ('keywords', models.CharField(max_length=100, null=True, blank=True)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=12, choices=[(b'TMS', b'TMS'), (b'WMS', b'WMS')])),
                ('name', models.CharField(max_length=50)),
                ('title', models.CharField(max_length=100, null=True, blank=True)),
                ('path', models.CharField(max_length=255, null=True, blank=True)),
                ('url', models.CharField(max_length=255, null=True, blank=True)),
                ('layers', models.CharField(max_length=255, null=True, blank=True)),
                ('projection', models.IntegerField(help_text=b'EPSG code')),
                ('dataset', models.ForeignKey(to='geoportal.Dataset', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
