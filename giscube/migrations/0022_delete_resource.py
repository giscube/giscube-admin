from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('giscube', '0021_delete_resources'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Resource',
        ),
    ]
