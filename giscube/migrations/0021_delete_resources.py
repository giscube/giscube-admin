from django.db import migrations


def delete_resources(apps, schema_editor):
    OldResource = apps.get_model('giscube', 'Resource')
    for old in OldResource.objects.all():
        old.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('giscube', '0020_dataset_resource'),
    ]
    operations = [
        migrations.RunPython(delete_resources, migrations.RunPython.noop),
    ]
