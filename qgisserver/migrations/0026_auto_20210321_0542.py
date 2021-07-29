# Generated by Django 2.2.17 on 2021-03-09 04:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('qgisserver', '0025_auto_20201127_1450'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='anonymous_view',
            field=models.BooleanField(default=False, verbose_name='anonymous users can view'),
        ),
        migrations.AddField(
            model_name='service',
            name='anonymous_write',
            field=models.BooleanField(default=False, verbose_name='anonymous users can write'),
        ),
        migrations.AddField(
            model_name='service',
            name='authenticated_user_view',
            field=models.BooleanField(default=False, verbose_name='authenticated users can view'),
        ),
        migrations.AddField(
            model_name='service',
            name='authenticated_user_write',
            field=models.BooleanField(default=False, verbose_name='authenticated users can write'),
        ),
        migrations.CreateModel(
            name='ServiceUserPermission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('can_view', models.BooleanField(default=True, verbose_name='Can view')),
                ('can_write', models.BooleanField(default=True, verbose_name='Can write')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_permissions', to='qgisserver.Service')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
            },
        ),
        migrations.CreateModel(
            name='ServiceGroupPermission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('can_view', models.BooleanField(default=True, verbose_name='Can view')),
                ('can_write', models.BooleanField(default=True, verbose_name='Can write')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.Group', verbose_name='Group')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_permissions', to='qgisserver.Service')),
            ],
            options={
                'verbose_name': 'Group',
                'verbose_name_plural': 'Groups',
            },
        ),
    ]
