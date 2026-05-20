from django.conf import settings

def giscube_settings(request):
    return {
        'GISCUBE_ENABLE_2FA': settings.GISCUBE_ENABLE_2FA,
    }
