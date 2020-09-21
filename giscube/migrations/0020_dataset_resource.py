import django.db.models.deletion
from django.db import migrations, models

import giscube.models
import giscube.storage
import giscube.validators


def migrate_dataset_resources(apps, schema_editor):
    OldResource = apps.get_model('giscube', 'Resource')
    Resource = apps.get_model('giscube', 'DatasetResource')

    for old in OldResource.objects.all():
        r = Resource()
        r.parent = old.dataset
        r.type = old.type
        r.name = old.name
        r.description = old.description
        r.title = old.title
        r.path = old.path
        r.url = old.url
        r.layers = old.layers
        r.projection = old.projection
        r.getfeatureinfo_support = old.getfeatureinfo_support
        r.single_image = old.single_image
        r.file = old.file
        r.save()


class Migration(migrations.Migration):

    dependencies = [
        ('giscube', '0019_giscubetransaction_error'),
    ]
    operations = [
        migrations.CreateModel(
            name='DatasetResource',
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
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resources', to='giscube.Dataset')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RunPython(migrate_dataset_resources, migrations.RunPython.noop),
    ]
