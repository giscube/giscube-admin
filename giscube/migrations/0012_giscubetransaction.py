# Generated by Django 2.2.10 on 2020-02-25 07:40

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('giscube', '0011_auto_20190507_0914'),
    ]

    operations = [
        migrations.CreateModel(
            name='GiscubeTransaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hash', models.CharField(max_length=32, verbose_name='Accessed ViewSet')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Access timestamp')),
                ('user', models.CharField(max_length=255, verbose_name='User')),
                ('url', models.CharField(max_length=255, verbose_name='URL')),
                ('request_headers', django.contrib.postgres.fields.jsonb.JSONField(default=dict, verbose_name='request headers')),
                ('request_body', models.TextField(blank=True, null=True, verbose_name='request body')),
                ('response_headers', django.contrib.postgres.fields.jsonb.JSONField(default=dict, verbose_name='request headers')),
                ('response_status_code', models.IntegerField(blank=True, null=True, verbose_name='response status code')),
                ('response_body', models.TextField(blank=True, null=True, verbose_name='response body')),
            ],
            options={
                'verbose_name': 'giscube transaction',
                'verbose_name_plural': 'giscube transactions',
            },
        )
    ]