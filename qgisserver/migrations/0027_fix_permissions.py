# Generated by Django 2.2.11 on 2020-05-06 05:08

from django.db import migrations


def migrate_to_anonymous_view(apps, schema_editor):
    ModelLayer = apps.get_model('qgisserver', 'Service')
    for layer in ModelLayer.objects.all():
        layer.anonymous_view = layer.visibility == 'public'
        layer.authenticated_user_view = layer.visibility == 'private'
        layer.save()


def undo_migrate_to_anonymous_view(apps, schema_editor):
    ModelLayer = apps.get_model('qgisserver', 'Service')
    for layer in ModelLayer.objects.all():
        if layer.anonymous_view:
            layer.visibility == 'public'
        else:
            layer.visibility == 'private'
        layer.save()


class Migration(migrations.Migration):

    dependencies = [
        ('qgisserver', '0026_auto_20210321_0542'),
    ]
    operations = [
        migrations.RunPython(migrate_to_anonymous_view, undo_migrate_to_anonymous_view),
        migrations.RemoveField(
            model_name='service',
            name='visibility',
        ),
    ]
