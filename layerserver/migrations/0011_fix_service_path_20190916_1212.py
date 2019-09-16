from django.db import migrations

from giscube.utils import unique_service_directory


def fix_service_path_null(apps, schema_editor):
    Model = apps.get_model('layerserver', 'DataBaseLayer')
    for x in Model.objects.filter(service_path__isnull=True):
        unique_service_directory(x)
        x.save()


class Migration(migrations.Migration):
    dependencies = [
        ('layerserver', '0010_auto_20190719_0929'),
    ]

    operations = [
        migrations.RunPython(fix_service_path_null,  migrations.RunPython.noop),
    ]
