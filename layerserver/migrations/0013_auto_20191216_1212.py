# Generated by Django 2.1.10 on 2019-12-16 11:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layerserver', '0012_auto_20190919_1004'),
    ]

    operations = [
        migrations.AlterField(
            model_name='databaselayerfield',
            name='widget',
            field=models.CharField(choices=[('auto', 'Auto'), ('choices', 'Choices, one line per value'), ('creationdate', 'Creation date'), ('creationdatetime', 'Creation datetime'), ('creationuser', 'Creation user'), ('date', 'Date'), ('datetime', 'Date time'), ('distinctvalues', 'Distinct values'), ('image', 'Image'), ('linkedfield', 'Linked Field'), ('modificationdate', 'Modification date'), ('modificationdatetime', 'Modification datetime'), ('modificationuser', 'Modification user'), ('sqlchoices', 'SQL choices')], default='auto', max_length=25, verbose_name='widget'),
        ),
    ]
