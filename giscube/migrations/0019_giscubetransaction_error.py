# Generated by Django 2.2.13 on 2020-09-05 08:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('giscube', '0018_auto_20200824_1159'),
    ]

    operations = [
        migrations.AddField(
            model_name='giscubetransaction',
            name='error',
            field=models.TextField(blank=True, null=True, verbose_name='error'),
        ),
    ]
