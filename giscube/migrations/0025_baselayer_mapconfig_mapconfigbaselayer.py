# Generated by Django 2.2.17 on 2021-06-15 11:22

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('giscube', '0024_auto_20210610_1311'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseLayer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('properties', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='properties')),
            ],
        ),
        migrations.CreateModel(
            name='MapConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='name')),
                ('center_lat', models.DecimalField(decimal_places=6, max_digits=8, verbose_name='center latitude')),
                ('center_lng', models.DecimalField(decimal_places=6, max_digits=9, verbose_name='center longitude')),
                ('initial_zoom', models.PositiveIntegerField(verbose_name='initial zoom')),
            ],
        ),
        migrations.CreateModel(
            name='MapConfigBaseLayer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField()),
                ('base_layer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='giscube.BaseLayer', verbose_name='base layer')),
                ('map_config', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='baselayers', to='giscube.MapConfig', verbose_name='map configuration')),
            ],
        ),
    ]
