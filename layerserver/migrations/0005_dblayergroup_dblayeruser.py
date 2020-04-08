# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-05-23 09:32


from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0008_alter_user_username_max_length'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('layerserver', '0004_databaselayer_databaselayerfield'),
    ]

    operations = [
        migrations.CreateModel(
            name='DBLayerGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('can_view', models.BooleanField(default=True, verbose_name='Can view')),
                ('can_add', models.BooleanField(default=True, verbose_name='Can add')),
                ('can_update', models.BooleanField(default=True, verbose_name='Can update')),
                ('can_delete', models.BooleanField(default=True, verbose_name='Can delete')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.Group', verbose_name='Group')),
                ('layer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_permissions', to='layerserver.DataBaseLayer')),
            ],
        ),
        migrations.CreateModel(
            name='DBLayerUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('can_view', models.BooleanField(default=True, verbose_name='Can view')),
                ('can_add', models.BooleanField(default=True, verbose_name='Can add')),
                ('can_update', models.BooleanField(default=True, verbose_name='Can update')),
                ('can_delete', models.BooleanField(default=True, verbose_name='Can delete')),
                ('layer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_permissions', to='layerserver.DataBaseLayer')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
        ),
    ]
