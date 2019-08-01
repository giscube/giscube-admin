from django.conf import settings


def remove_app_url(path):
    if settings.APP_URL != '':
        if path.startswith(settings.APP_URL):
            path = path[len(settings.APP_URL):]
    return path


def url_slash_join(*args):
    return '/'.join([(u.strip('/') if index + 1 < len(args) else u.lstrip('/')) for index, u in enumerate(args)])
