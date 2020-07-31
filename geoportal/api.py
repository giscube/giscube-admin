from django.urls import reverse

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    data = {
        'username': request.user.username,
        'admin_url': request.build_absolute_uri(reverse('admin:index')),
        'is_staff': request.user.is_staff,
    }
    return Response(data)
