# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-04-10 12:01


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('imageserver', '0005_auto_20180301_0907'),
    ]

    operations = [
        migrations.AlterField(
            model_name='service',
            name='keywords',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
