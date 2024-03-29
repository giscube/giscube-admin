# Generated by Django 2.2.27 on 2022-07-14 07:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('layerserver', '0031_auto_20210610_1311'),
    ]

    operations = [
        migrations.CreateModel(
            name='GeoJsonFilter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=100, null=True, verbose_name='title')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('filter', models.CharField(blank=True, max_length=255, null=True, verbose_name='filter')),
                ('layer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='filters', to='layerserver.GeoJsonLayer')),
            ],
        ),
    ]
