# Generated by Django 2.2.9 on 2020-01-15 11:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('geoportal', '0012_dataset_legend'),
        ('giscube', '0014_dataset'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resource',
            name='dataset',
        ),
        migrations.DeleteModel(
            name='Dataset',
        ),
        migrations.DeleteModel(
            name='Resource',
        ),
    ]