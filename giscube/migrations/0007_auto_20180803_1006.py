# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-08-03 10:06


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('giscube', '0006_server'),
    ]

    operations = [
        migrations.AlterField(
            model_name='server',
            name='url',
            field=models.URLField(blank=True, null=True),
        ),
    ]
