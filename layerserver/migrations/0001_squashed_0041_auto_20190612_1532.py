# Generated by Django 2.1.7 on 2019-06-12 13:33

import colorfield.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import layerserver.models


# Functions from the following migrations need manual copying.
# Move them and any dependencies into this file, then update the
# RunPython operations to refer to the local versions:
# layerserver.migrations.0035_auto_20190427_0620

class Migration(migrations.Migration):

    replaces = [('layerserver', '0001_initial'), ('layerserver', '0002_geojsonlayer_generated_on'), ('layerserver', '0003_auto_20180521_1232'), ('layerserver', '0004_databaselayer_databaselayerfield'), ('layerserver', '0005_dblayergroup_dblayeruser'), ('layerserver', '0006_auto_20180525_0953'), ('layerserver', '0007_auto_20180525_1311'), ('layerserver', '0008_auto_20180529_1051'), ('layerserver', '0009_auto_20180529_1111'), ('layerserver', '0010_auto_20180601_0710'), ('layerserver', '0011_auto_20180726_0745'), ('layerserver', '0012_auto_20181207_1510'), ('layerserver', '0013_auto_20181210_1133'), ('layerserver', '0014_auto_20190116_1110'), ('layerserver', '0015_auto_20190215_0800'), ('layerserver', '0016_auto_20190218_0848'), ('layerserver', '0017_auto_20190305_1011'), ('layerserver', '0018_auto_20190319_1758'), ('layerserver', '0019_auto_20190320_1014'), ('layerserver', '0020_geojsonlayer_headers'), ('layerserver', '0021_auto_20190320_1420'), ('layerserver', '0022_auto_20190320_1452'), ('layerserver', '0023_auto_20190325_1318'), ('layerserver', '0024_auto_20190326_1337'), ('layerserver', '0025_auto_20190326_1352'), ('layerserver', '0026_auto_20190326_1356'), ('layerserver', '0027_databaselayerfield_readonly'), ('layerserver', '0028_auto_20190404_2030'), ('layerserver', '0029_auto_20190406_1352'), ('layerserver', '0030_auto_20190411_0621'), ('layerserver', '0031_auto_20190416_1503'), ('layerserver', '0032_auto_20190417_1308'), ('layerserver', '0033_geojsonlayer_fields'), ('layerserver', '0034_databaselayerfield_blank'), ('layerserver', '0035_auto_20190427_0620'), ('layerserver', '0036_auto_20190507_0914'), ('layerserver', '0037_auto_20190514_0812'), ('layerserver', '0038_auto_20190516_0814'), ('layerserver', '0039_auto_20190516_1036'), ('layerserver', '0040_auto_20190521_1443'), ('layerserver', '0041_auto_20190612_1532')]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('qgisserver', '0009_auto_20180425_1526'),
        ('giscube', '0003_dbconnection'),
        ('auth', '0008_alter_user_username_max_length'),
        ('giscube', '0002_update'),
        ('giscube', '0004_dbconnection_alias'),
    ]

    operations = [
        migrations.CreateModel(
            name='GeoJsonLayer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('title', models.CharField(blank=True, max_length=100, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('keywords', models.CharField(blank=True, max_length=200, null=True)),
                ('active', models.BooleanField(default=True, help_text='Enable/disable usage')),
                ('visibility', models.CharField(choices=[('private', 'Private'), ('public', 'Public')], default='private', help_text="visibility='Private' restricts usage to authenticated users", max_length=10)),
                ('visible_on_geoportal', models.BooleanField(default=False)),
                ('shapetype', models.CharField(blank=True, choices=[('marker', 'Marker'), ('line', 'Line'), ('polygon', 'Polygon'), ('circle', 'Circle')], max_length=20, null=True)),
                ('shape_radius', models.CharField(blank=True, max_length=50, null=True)),
                ('stroke_color', models.CharField(blank=True, default='#FF3333', max_length=50, null=True)),
                ('stroke_width', models.CharField(blank=True, default='1', max_length=50, null=True)),
                ('stroke_dash_array', models.CharField(blank=True, default='', max_length=50, null=True)),
                ('fill_color', models.CharField(blank=True, default='#FFC300', max_length=50, null=True)),
                ('fill_opacity', models.CharField(blank=True, default='1', max_length=50, null=True)),
                ('url', models.CharField(blank=True, max_length=255, null=True)),
                ('data_file', models.FileField(blank=True, null=True, upload_to=layerserver.models.geojsonlayer_upload_path)),
                ('service_path', models.CharField(max_length=255)),
                ('cache_time', models.IntegerField(blank=True, help_text='In seconds', null=True)),
                ('last_fetch_on', models.DateTimeField(blank=True, null=True)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='giscube.Category')),
                ('generated_on', models.DateTimeField(blank=True, null=True)),
                ('headers', models.TextField(blank=True, null=True)),
                ('popup', models.TextField(blank=True, null=True)),
                ('icon', models.CharField(blank=True, max_length=255, null=True)),
                ('icon_color', models.CharField(blank=True, max_length=50, null=True)),
                ('icon_type', models.CharField(blank=True, choices=[('fa', 'fa'), ('img', 'img')], max_length=100, null=True)),
                ('marker_color', models.CharField(blank=True, max_length=50, null=True)),
                ('fields', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'GeoJSONLayer',
                'verbose_name_plural': 'GeoJSONLayers',
            },
        ),
        migrations.CreateModel(
            name='DataBaseLayer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=100, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('keywords', models.CharField(blank=True, max_length=200, null=True)),
                ('active', models.BooleanField(default=True)),
                ('visibility', models.CharField(choices=[('private', 'Private'), ('public', 'Public')], default='private', max_length=10)),
                ('visible_on_geoportal', models.BooleanField(default=False)),
                ('shapetype', models.CharField(blank=True, choices=[('marker', 'Marker'), ('line', 'Line'), ('polygon', 'Polygon'), ('Circle', 'Circle')], max_length=20, null=True)),
                ('shape_radius', models.IntegerField(blank=True, null=True)),
                ('stroke_color', colorfield.fields.ColorField(blank=True, default=b'#FF3333', max_length=18, null=True)),
                ('stroke_width', models.IntegerField(blank=True, default=1, null=True)),
                ('stroke_dash_array', models.CharField(blank=True, default='', max_length=25, null=True)),
                ('fill_color', colorfield.fields.ColorField(blank=True, default=b'#FFC300', max_length=18, null=True)),
                ('fill_opacity', models.DecimalField(blank=True, decimal_places=1, default=1, max_digits=2, null=True)),
                ('slug', models.SlugField(max_length=255, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('table', models.CharField(max_length=255)),
                ('pk_field', models.CharField(max_length=255)),
                ('geom_field', models.CharField(max_length=255)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='giscube.Category')),
                ('db_connection', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='layers', to='giscube.DBConnection')),
            ],
            options={
                'verbose_name': 'DataBaseLayer',
                'verbose_name_plural': 'DataBaseLayers',
            },
        ),
        migrations.CreateModel(
            name='DataBaseLayerField',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('label', models.CharField(blank=True, max_length=255, null=True)),
                ('enabled', models.BooleanField(default=True)),
                ('layer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fields', to='layerserver.DataBaseLayer')),
                ('fullsearch', models.BooleanField(default=True)),
                ('search', models.BooleanField(default=True)),
                ('widget_options', models.TextField(blank=True, null=True)),
                ('widget', models.CharField(choices=[('auto', 'Auto'), ('choices', 'Choices, one line per value'), ('image', 'Image'), ('linkedfield', 'Linked Field'), ('sqlchoices', 'SQL choices')], default='auto', max_length=25)),
                ('readonly', models.BooleanField(default=False)),
                ('blank', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Field',
                'verbose_name_plural': 'Fields',
                'ordering': ['layer', 'name'],
            },
        ),
        migrations.CreateModel(
            name='DBLayerGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('can_view', models.BooleanField(default=True, verbose_name='Can view')),
                ('can_add', models.BooleanField(default=True, verbose_name='Can add')),
                ('can_update', models.BooleanField(default=True, verbose_name='Can update')),
                ('can_delete', models.BooleanField(default=True, verbose_name='Can delete')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.Group', verbose_name='Group')),
                ('layer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_permissions', to='layerserver.DataBaseLayer')),
            ],
            options={
                'verbose_name': 'Group',
                'verbose_name_plural': 'Groups',
            },
        ),
        migrations.CreateModel(
            name='DBLayerUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('can_view', models.BooleanField(default=True, verbose_name='Can view')),
                ('can_add', models.BooleanField(default=True, verbose_name='Can add')),
                ('can_update', models.BooleanField(default=True, verbose_name='Can update')),
                ('can_delete', models.BooleanField(default=True, verbose_name='Can delete')),
                ('layer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_permissions', to='layerserver.DataBaseLayer')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
            },
        ),
        migrations.AddField(
            model_name='databaselayer',
            name='srid',
            field=models.IntegerField(default=4326),
        ),
        migrations.AddField(
            model_name='databaselayer',
            name='anonymous_add',
            field=models.BooleanField(default=False, verbose_name='Can add'),
        ),
        migrations.AddField(
            model_name='databaselayer',
            name='anonymous_delete',
            field=models.BooleanField(default=False, verbose_name='Can delete'),
        ),
        migrations.AddField(
            model_name='databaselayer',
            name='anonymous_update',
            field=models.BooleanField(default=False, verbose_name='Can update'),
        ),
        migrations.AddField(
            model_name='databaselayer',
            name='anonymous_view',
            field=models.BooleanField(default=False, verbose_name='Can view'),
        ),
        migrations.CreateModel(
            name='DataBaseLayerReference',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'Reference',
                'verbose_name_plural': 'References',
            },
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='db_connection',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='layers', to='giscube.DBConnection', verbose_name='Database connection'),
        ),
        migrations.AddField(
            model_name='databaselayerreference',
            name='layer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='references', to='layerserver.DataBaseLayer'),
        ),
        migrations.AddField(
            model_name='databaselayerreference',
            name='service',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='qgisserver.Service'),
        ),
        migrations.AlterUniqueTogether(
            name='databaselayerreference',
            unique_together={('layer', 'service')},
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='geom_field',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='fill_color',
            field=colorfield.fields.ColorField(blank=True, default='#FFC300', max_length=18, null=True),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='stroke_color',
            field=colorfield.fields.ColorField(blank=True, default='#FF3333', max_length=18, null=True),
        ),
        migrations.AddField(
            model_name='databaselayer',
            name='max_page_size',
            field=models.IntegerField(blank=True, help_text='Default value is 1000', null=True),
        ),
        migrations.AddField(
            model_name='databaselayer',
            name='page_size',
            field=models.IntegerField(blank=True, help_text='Default value is 50. Value 0 disables pagination.', null=True),
        ),
        migrations.RemoveField(
            model_name='databaselayer',
            name='visibility',
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='active',
            field=models.BooleanField(default=True, help_text='Enable/disable usage'),
        ),
        migrations.AddField(
            model_name='databaselayer',
            name='popup',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='databaselayer',
            name='form_fields',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='databaselayer',
            name='list_fields',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='databaselayer',
            name='allow_page_size_0',
            field=models.BooleanField(default=False, verbose_name='Allow page_size=0 (Disables pagination)'),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='geom_field',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='pk_field',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='databaselayer',
            name='icon',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='databaselayer',
            name='icon_color',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='databaselayer',
            name='icon_type',
            field=models.CharField(blank=True, choices=[('fa', 'fa'), ('img', 'img')], max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='databaselayer',
            name='marker_color',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='fill_color',
            field=models.CharField(blank=True, default='#FFC300', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='shapetype',
            field=models.CharField(blank=True, choices=[('marker', 'Marker'), ('line', 'Line'), ('polygon', 'Polygon'), ('circle', 'Circle')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='stroke_color',
            field=models.CharField(blank=True, default='#FF3333', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='fill_opacity',
            field=models.CharField(blank=True, default='1', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='shape_radius',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='stroke_dash_array',
            field=models.CharField(blank=True, default='', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='stroke_width',
            field=models.CharField(blank=True, default='1', max_length=50, null=True),
        ),
        migrations.CreateModel(
            name='DataBaseLayerStyleRule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shape_radius', models.CharField(blank=True, max_length=50, null=True)),
                ('stroke_color', models.CharField(blank=True, default='#FF3333', max_length=50, null=True)),
                ('stroke_width', models.CharField(blank=True, default='1', max_length=50, null=True)),
                ('stroke_dash_array', models.CharField(blank=True, default='', max_length=50, null=True)),
                ('fill_color', models.CharField(blank=True, default='#FFC300', max_length=50, null=True)),
                ('fill_opacity', models.CharField(blank=True, default='1', max_length=50, null=True)),
                ('marker_color', models.CharField(blank=True, max_length=50, null=True)),
                ('icon_type', models.CharField(blank=True, choices=[('fa', 'fa'), ('img', 'img')], max_length=100, null=True)),
                ('icon', models.CharField(blank=True, max_length=255, null=True)),
                ('icon_color', models.CharField(blank=True, max_length=50, null=True)),
                ('field', models.CharField(max_length=50)),
                ('comparator', models.CharField(choices=[('=', '='), ('!=', '!='), ('>', '>'), ('>=', '>='), ('<', '<'), ('<=', '<=')], max_length=3)),
                ('value', models.CharField(max_length=255)),
                ('order', models.PositiveIntegerField(blank=True, null=True)),
                ('layer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rules', to='layerserver.DataBaseLayer')),
            ],
            options={
                'ordering': ('layer', 'order'),
                'verbose_name_plural': 'Style rules',
                'verbose_name': 'Style rule',
            },
        ),
        migrations.CreateModel(
            name='GeoJsonLayerStyleRule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shape_radius', models.CharField(blank=True, max_length=50, null=True)),
                ('stroke_color', models.CharField(blank=True, default='#FF3333', max_length=50, null=True)),
                ('stroke_width', models.CharField(blank=True, default='1', max_length=50, null=True)),
                ('stroke_dash_array', models.CharField(blank=True, default='', max_length=50, null=True)),
                ('fill_color', models.CharField(blank=True, default='#FFC300', max_length=50, null=True)),
                ('fill_opacity', models.CharField(blank=True, default='1', max_length=50, null=True)),
                ('marker_color', models.CharField(blank=True, max_length=50, null=True)),
                ('icon_type', models.CharField(blank=True, choices=[('fa', 'fa'), ('img', 'img')], max_length=100, null=True)),
                ('icon', models.CharField(blank=True, max_length=255, null=True)),
                ('icon_color', models.CharField(blank=True, max_length=50, null=True)),
                ('field', models.CharField(max_length=50)),
                ('comparator', models.CharField(choices=[('=', '='), ('!=', '!='), ('>', '>'), ('>=', '>='), ('<', '<'), ('<=', '<=')], max_length=3)),
                ('value', models.CharField(blank=True, max_length=255, null=True)),
                ('order', models.PositiveIntegerField(blank=True, null=True)),
                ('layer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rules', to='layerserver.GeoJsonLayer')),
            ],
            options={
                'ordering': ('layer', 'order'),
                'verbose_name_plural': 'Style rules',
                'verbose_name': 'Style rule',
            },
        ),
        # migrations.RunPython(
        #     code=layerserver.migrations.0035_auto_20190427_0620.update_name,
        #     reverse_code=layerserver.migrations.0035_auto_20190427_0620.reverse_func,
        # ),
        migrations.RemoveField(
            model_name='databaselayer',
            name='slug',
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='name',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='allow_page_size_0',
            field=models.BooleanField(default=False, verbose_name='Allow page size=0 (Disables pagination)'),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='form_fields',
            field=models.TextField(blank=True, null=True, verbose_name='form fields'),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='geom_field',
            field=models.CharField(max_length=255, verbose_name='geom field'),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='list_fields',
            field=models.TextField(blank=True, null=True, verbose_name='list fields'),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='max_page_size',
            field=models.IntegerField(blank=True, help_text='Default value is 1000', null=True, verbose_name='maximum page size'),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='name',
            field=models.CharField(max_length=255, unique=True, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='page_size',
            field=models.IntegerField(blank=True, help_text='Default value is 50. Value 0 disables pagination.', null=True, verbose_name='page size'),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='pk_field',
            field=models.CharField(blank=True, max_length=255, verbose_name='pk field'),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='shapetype',
            field=models.CharField(blank=True, choices=[('marker', 'Marker'), ('line', 'Line'), ('polygon', 'Polygon'), ('circle', 'Circle'), ('image', 'Image')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='srid',
            field=models.IntegerField(default=4326, verbose_name='srid'),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='table',
            field=models.CharField(max_length=255, verbose_name='table'),
        ),
        migrations.AlterField(
            model_name='databaselayerfield',
            name='blank',
            field=models.BooleanField(default=True, verbose_name='blank'),
        ),
        migrations.AlterField(
            model_name='databaselayerfield',
            name='enabled',
            field=models.BooleanField(default=True, verbose_name='enabled'),
        ),
        migrations.AlterField(
            model_name='databaselayerfield',
            name='fullsearch',
            field=models.BooleanField(default=True, verbose_name='full search'),
        ),
        migrations.AlterField(
            model_name='databaselayerfield',
            name='label',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='label'),
        ),
        migrations.AlterField(
            model_name='databaselayerfield',
            name='name',
            field=models.CharField(max_length=255, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='databaselayerfield',
            name='readonly',
            field=models.BooleanField(default=False, verbose_name='readonly'),
        ),
        migrations.AlterField(
            model_name='databaselayerfield',
            name='search',
            field=models.BooleanField(default=True, verbose_name='search'),
        ),
        migrations.AlterField(
            model_name='databaselayerfield',
            name='widget',
            field=models.CharField(choices=[('auto', 'Auto'), ('choices', 'Choices, one line per value'), ('date', 'Date'), ('image', 'Image'), ('linkedfield', 'Linked Field'), ('sqlchoices', 'SQL choices')], default='auto', max_length=25, verbose_name='widget'),
        ),
        migrations.AlterField(
            model_name='databaselayerfield',
            name='widget_options',
            field=models.TextField(blank=True, null=True, verbose_name='widget options'),
        ),
        migrations.AlterField(
            model_name='databaselayerstylerule',
            name='comparator',
            field=models.CharField(choices=[('=', '='), ('!=', '!='), ('>', '>'), ('>=', '>='), ('<', '<'), ('<=', '<=')], max_length=3, verbose_name='comparator'),
        ),
        migrations.AlterField(
            model_name='databaselayerstylerule',
            name='field',
            field=models.CharField(max_length=50, verbose_name='field'),
        ),
        migrations.AlterField(
            model_name='databaselayerstylerule',
            name='order',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='order'),
        ),
        migrations.AlterField(
            model_name='databaselayerstylerule',
            name='value',
            field=models.CharField(max_length=255, verbose_name='value'),
        ),
        migrations.AlterField(
            model_name='geojsonlayer',
            name='cache_time',
            field=models.IntegerField(blank=True, help_text='In seconds', null=True, verbose_name='cache time'),
        ),
        migrations.AlterField(
            model_name='geojsonlayer',
            name='data_file',
            field=models.FileField(blank=True, null=True, upload_to=layerserver.models.geojsonlayer_upload_path, verbose_name='data file'),
        ),
        migrations.AlterField(
            model_name='geojsonlayer',
            name='generated_on',
            field=models.DateTimeField(blank=True, null=True, verbose_name='generated on'),
        ),
        migrations.AlterField(
            model_name='geojsonlayer',
            name='headers',
            field=models.TextField(blank=True, null=True, verbose_name='headers'),
        ),
        migrations.AlterField(
            model_name='geojsonlayer',
            name='last_fetch_on',
            field=models.DateTimeField(blank=True, null=True, verbose_name='last fetch on'),
        ),
        migrations.AlterField(
            model_name='geojsonlayer',
            name='service_path',
            field=models.CharField(max_length=255, verbose_name='service path'),
        ),
        migrations.AlterField(
            model_name='geojsonlayer',
            name='shapetype',
            field=models.CharField(blank=True, choices=[('marker', 'Marker'), ('line', 'Line'), ('polygon', 'Polygon'), ('circle', 'Circle'), ('image', 'Image')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='geojsonlayer',
            name='url',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='url'),
        ),
        migrations.AlterField(
            model_name='geojsonlayer',
            name='visibility',
            field=models.CharField(choices=[('private', 'Private'), ('public', 'Public')], default='private', help_text="visibility='Private' restricts usage to authenticated users", max_length=10, verbose_name='visibility'),
        ),
        migrations.AlterField(
            model_name='geojsonlayerstylerule',
            name='comparator',
            field=models.CharField(choices=[('=', '='), ('!=', '!='), ('>', '>'), ('>=', '>='), ('<', '<'), ('<=', '<=')], max_length=3, verbose_name='comparator'),
        ),
        migrations.AlterField(
            model_name='geojsonlayerstylerule',
            name='field',
            field=models.CharField(max_length=50, verbose_name='field'),
        ),
        migrations.AlterField(
            model_name='geojsonlayerstylerule',
            name='order',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='order'),
        ),
        migrations.AlterField(
            model_name='geojsonlayerstylerule',
            name='value',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='value'),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='shapetype',
            field=models.CharField(blank=True, choices=[('marker', 'Marker'), ('line', 'Line'), ('polygon', 'Polygon'), ('circle', 'Circle'), ('image', 'Image')], max_length=20, null=True, verbose_name='Shape Type'),
        ),
        migrations.AlterField(
            model_name='geojsonlayer',
            name='shapetype',
            field=models.CharField(blank=True, choices=[('marker', 'Marker'), ('line', 'Line'), ('polygon', 'Polygon'), ('circle', 'Circle'), ('image', 'Image')], max_length=20, null=True, verbose_name='Shape Type'),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='geom_field',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='geom field'),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='srid',
            field=models.IntegerField(blank=True, default=4326, null=True, verbose_name='srid'),
        ),
        migrations.AlterField(
            model_name='databaselayer',
            name='srid',
            field=models.IntegerField(blank=True, null=True, verbose_name='srid'),
        ),
        migrations.CreateModel(
            name='DataBaseLayerVirtualField',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('label', models.CharField(blank=True, max_length=255, null=True, verbose_name='label')),
                ('enabled', models.BooleanField(default=True, verbose_name='enabled')),
                ('widget', models.CharField(choices=[('relation1n', '1:N Relation'), ('linkedfield', 'Linked Field')], max_length=25, verbose_name='widget')),
                ('widget_options', models.TextField(blank=True, null=True, verbose_name='widget options')),
                ('layer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='virtual_fields', to='layerserver.DataBaseLayer')),
            ],
            options={
                'ordering': ['layer', 'name'],
                'verbose_name_plural': 'Virtual Fields',
                'verbose_name': 'Virtual Field',
            },
        ),
        migrations.AlterField(
            model_name='databaselayerfield',
            name='widget',
            field=models.CharField(choices=[('auto', 'Auto'), ('choices', 'Choices, one line per value'), ('date', 'Date'), ('datetime', 'Date time'), ('image', 'Image'), ('linkedfield', 'Linked Field'), ('sqlchoices', 'SQL choices')], default='auto', max_length=25, verbose_name='widget'),
        ),
        migrations.AddField(
            model_name='geojsonlayer',
            name='max_outdated_time',
            field=models.PositiveIntegerField(blank=True, help_text='Maximum outdated time in seconds for the cache file', null=True, verbose_name='maximum outdated time'),
        ),
        migrations.AlterField(
            model_name='geojsonlayer',
            name='cache_time',
            field=models.PositiveIntegerField(blank=True, help_text='time in seconds where the file is served from cache', null=True, verbose_name='cache time'),
        ),
        migrations.AlterField(
            model_name='geojsonlayer',
            name='cache_time',
            field=models.PositiveIntegerField(blank=True, help_text='Time in seconds where the file is served from cache', null=True, verbose_name='cache time'),
        ),
    ]
