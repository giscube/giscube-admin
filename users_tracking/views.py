from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED

from .models import VisorUserTrack


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    else:
        return request.META.get('REMOTE_ADDR')


def get_username(request):
    if request.user.username:
        return request.user.username
    else:
        return 'Unknown'


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def visor_user_tracking(request):
    ip = get_client_ip(request)
    username = get_username(request)
    now = timezone.now()
    user_track = VisorUserTrack(username=username, datetime=now, ip=ip)
    user_track.save()
    return Response('User registered', status=HTTP_201_CREATED)
