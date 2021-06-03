# Generated by Django 2.2.17 on 2021-06-10 11:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('giscube', '0023_auto_20201119_0610'),
    ]

    operations = [
        migrations.AddField(
            model_name='datasetresource',
            name='layer_list',
            field=models.TextField(blank=True, null=True, verbose_name='layer_list'),
        ),
        migrations.AddField(
            model_name='datasetresource',
            name='separate_layers',
            field=models.BooleanField(default=False, verbose_name='use separate layers'),
        ),
    ]
