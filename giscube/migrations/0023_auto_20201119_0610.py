# Generated by Django 2.2.16 on 2020-11-19 05:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('giscube', '0022_datasetresource_content_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datasetresource',
            name='content_type',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='format'),
        ),
    ]