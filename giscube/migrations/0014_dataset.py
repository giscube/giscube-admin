# Generated by Django 2.2.11 on 2020-05-05 12:06

# Generated by Django 2.2.10 on 2020-03-17 10:18
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import F

import giscube.models
import giscube.storage
import giscube.validators


def migrate_dataset(apps, schema_editor):
    OldDataset = apps.get_model('geoportal', 'Dataset')
    Dataset = apps.get_model('giscube', 'Dataset')
    Resource = apps.get_model('giscube', 'Resource')

    for old_d in OldDataset.objects.all():
        if not Dataset.objects.filter(name=old_d.name).exists():
            d = Dataset()
            d.category = old_d.category
            d.name = old_d.name
            d.title = old_d.title
            d.description = old_d.title
            d.keywords = old_d.keywords
            d.active = old_d.active
            d.options = old_d.options
            d.legend = old_d.legend
            d.visible_on_geoportal = old_d.active
            d.save()
            for old_r in old_d.resources.all():
                r = Resource()
                r.dataset = d
                r.type = old_r.type
                r.name = old_r.name
                r.title = old_r.title
                r.path = old_r.path
                r.url = old_r.url
                r.layers = old_r.layers
                r.projection = old_r.projection
                r.getfeatureinfo_support = old_r.getfeatureinfo_support
                r.single_image = old_r.single_image
                r.save()


def set_anonymous_view(apps, schema_editor):
    Dataset = apps.get_model('giscube', 'Dataset')
    Dataset.objects.update(anonymous_view=F('active'))


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('geoportal', '0012_dataset_legend'),
        ('giscube', '0013_userasset'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='name')),
                ('title', models.CharField(blank=True, max_length=100, null=True, verbose_name='title')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('keywords', models.CharField(blank=True, max_length=200, null=True, verbose_name='keywords')),
                ('active', models.BooleanField(default=True, help_text='Enable/disable usage', verbose_name='active')),
                ('visible_on_geoportal', models.BooleanField(default=False, verbose_name='visible on geoportal')),
                ('options', models.TextField(blank=True, help_text='json format. Ex: {"maxZoom": 20}', null=True, validators=[giscube.validators.validate_options_json_format], verbose_name='options')),
                ('legend', models.TextField(blank=True, null=True, verbose_name='legend')),
                ('anonymous_view', models.BooleanField(default=False, verbose_name='anonymous users can view')),
                ('authenticated_user_view', models.BooleanField(default=False, verbose_name='authenticated users can view')),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='datasets', to='giscube.Category')),
            ],
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('TMS', 'TMS'), ('WMS', 'WMS'), ('document', 'Document'), ('url', 'URL')], max_length=12, verbose_name='type')),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('title', models.CharField(blank=True, max_length=100, null=True, verbose_name='title')),
                ('path', models.CharField(blank=True, max_length=255, null=True, verbose_name='path')),
                ('url', models.CharField(blank=True, max_length=255, null=True, verbose_name='url')),
                ('file', models.FileField(blank=True, max_length=255, null=True, storage=giscube.storage.OverwriteStorage(), upload_to=giscube.model_mixins.resource_upload_to, verbose_name='file')),
                ('layers', models.CharField(blank=True, max_length=255, null=True, verbose_name='layers')),
                ('projection', models.IntegerField(blank=True, help_text='EPSG code', null=True, verbose_name='projection')),
                ('getfeatureinfo_support', models.BooleanField(default=True, verbose_name='WMS GetFeatureInfo support')),
                ('single_image', models.BooleanField(default=False, verbose_name='use single image')),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resources', to='giscube.Dataset')),
            ],
        ),
        migrations.RunPython(migrate_dataset, migrations.RunPython.noop),
        migrations.RunPython(set_anonymous_view, migrations.RunPython.noop),
        migrations.CreateModel(
            name='DatasetGroupPermission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('can_view', models.BooleanField(default=True, verbose_name='Can view')),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_permissions', to='giscube.Dataset')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.Group', verbose_name='Group')),
            ],
            options={
                'verbose_name': 'Group',
                'verbose_name_plural': 'Groups',
            },
        ),
        migrations.CreateModel(
            name='DatasetUserPermission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('can_view', models.BooleanField(default=True, verbose_name='Can view')),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_permissions', to='giscube.Dataset')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
            },
        ),
    ]
