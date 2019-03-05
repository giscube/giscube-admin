# -*- coding: utf-8 -*-


from django.db import models, migrations
import imageserver.models


class Migration(migrations.Migration):

    dependencies = [
        ('imageserver', '0002_auto_20150216_1805'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='layer_path',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='layer',
            name='mask_path',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='namedmask',
            name='mask_path',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='layer',
            name='mask',
            field=models.FileField(null=True, upload_to=imageserver.models.get_mask_upload_path, blank=True),
        ),
    ]
