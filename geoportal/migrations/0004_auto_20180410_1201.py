# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-04-10 12:01


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geoportal', '0003_auto_20180227_1814'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='keywords',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
