# Generated by Django 2.2.11 on 2020-05-05 12:06

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('giscube', '0012_giscubetransaction'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userasset',
            name='created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='creation datetime'),
        )
    ]
