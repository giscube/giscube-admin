from django.apps import apps


def giscube_search_get_app_modules():
    """Return the Python module for each installed app"""
    return [i.module for i in apps.get_app_configs()]
