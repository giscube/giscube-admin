# Generated by Django 2.1.7 on 2019-03-25 13:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geoportal', '0007_auto_20190305_1011'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataset',
            name='active',
            field=models.BooleanField(default=True, help_text='Enable/disable usage'),
        ),
    ]
