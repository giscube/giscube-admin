from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('giscube', '0019_giscubetransaction_error'),
    ]
    operations = [
        migrations.AlterField('Resource', 'id', models.IntegerField(verbose_name='ID')),
        migrations.RenameField('Resource', 'dataset', 'parent'),
        migrations.RenameModel('Resource', 'DatasetResource'),
        migrations.AlterField('DatasetResource', 'id', models.AutoField(
            auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
    ]
