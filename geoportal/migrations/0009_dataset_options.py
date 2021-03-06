# Generated by Django 2.1.7 on 2019-04-29 07:50

from django.db import migrations, models
import giscube.validators


class Migration(migrations.Migration):

    dependencies = [
        ('geoportal', '0008_auto_20190325_1318'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='options',
            field=models.TextField(blank=True, help_text='json format. Ex: {"maxZoom": 20}', null=True, validators=[giscube.validators.validate_options_json_format], verbose_name='options'),
        ),
    ]
