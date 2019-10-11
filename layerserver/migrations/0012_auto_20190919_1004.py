# Generated by Django 2.1.10 on 2019-09-19 08:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layerserver', '0011_fix_service_path_20190916_1212'),
    ]

    operations = [
        migrations.AddField(
            model_name='databaselayerreference',
            name='format',
            field=models.CharField(choices=[('image/png', 'PNG'), ('image/jpeg', 'JPEG')], default='image/jpeg', max_length=25, verbose_name='format'),
        ),
        migrations.AddField(
            model_name='databaselayerreference',
            name='transparent',
            field=models.BooleanField(null=True, verbose_name='transparent'),
        ),
    ]
