# Generated by Django 2.1.7 on 2019-03-26 13:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('layerserver', '0023_auto_20190325_1318'),
    ]

    operations = [
        migrations.AddField(
            model_name='databaselayer',
            name='popup',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='geojsonlayer',
            name='popup',
            field=models.TextField(blank=True, null=True),
        ),
    ]
