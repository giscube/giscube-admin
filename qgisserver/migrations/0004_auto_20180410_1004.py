# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-04-10 10:04


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('qgisserver', '0003_project'),
    ]

    operations = [
        migrations.RenameField(
            model_name='service',
            old_name='project',
            new_name='project_file',
        ),
    ]
