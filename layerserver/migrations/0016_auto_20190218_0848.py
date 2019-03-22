# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-02-18 08:48


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layerserver', '0015_auto_20190215_0800'),
    ]

    operations = [
        migrations.AlterField(
            model_name='databaselayerfield',
            name='widget',
            field=models.CharField(choices=[('auto', 'Auto'), ('choices', 'Choices, one line per value'), ('image', 'Image'), ('linkedfield', 'Linked Field'), ('sqlchoices', 'SQL choices')], default='auto', max_length=25),
        ),
    ]
