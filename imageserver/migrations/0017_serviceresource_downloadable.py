# Generated by Django 3.0.10 on 2020-09-21 13:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('imageserver', '0016_serviceresource'),
    ]

    operations = [
        migrations.AddField(
            model_name='serviceresource',
            name='downloadable',
            field=models.BooleanField(default=False, verbose_name='downloadable'),
        ),
    ]
