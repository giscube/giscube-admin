# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2018-02-27 13:22


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qgisserver', '0002_auto_20150216_1807'),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('data', models.TextField()),
            ],
        ),
    ]
