from django.conf import settings


def full_url(url):
    return url_slash_join(settings.SITE_URL, settings.APP_URL, url)


def remove_app_url(path):
    if settings.APP_URL != '':
        if path.startswith(settings.APP_URL):
            path = path[len(settings.APP_URL):]
    return path


def url_slash_join(*args):
    args = list(filter(None, args))
    return '/'.join([(u.strip('/') if index + 1 < len(args) else u.lstrip('/')) for index, u in enumerate(args)])
