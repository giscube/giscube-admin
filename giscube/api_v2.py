from url_filter.filtersets import ModelFilterSet

from django.contrib.auth.models import User
from django.db.models.functions import Concat
from django.http import HttpResponse
from django.utils import timezone

from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated

from giscube.permissions import FixedDjangoModelPermissions

from .models import AccessLog, Category, UsersLog
from .serializers import CategorySerializer, UsersLogSerializer
from .utils import get_client_ip


class CategoryFilter(ModelFilterSet):
    class Meta:
        model = Category
        fiels = '__all__'


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = []
    serializer_class = CategorySerializer
    permission_classes = (FixedDjangoModelPermissions,)

    def get_queryset(self):
        qs = Category.objects.all()
        qs = CategoryFilter(data=self.request.query_params, queryset=qs)
        qs = qs.filter()
        # Sort categories setting parents first
        qs = qs.annotate(custom_order=Concat('parent__name', 'name'))
        qs = qs.order_by('custom_order')
        return qs


def list_userslog(request):
    date_init = request.GET.get('date_init')
    date_end = request.GET.get('date_end')

    if not date_init or not date_end:
        return HttpResponse('date_init and date_end parameters are required', status=400)

    users_log = UsersLog.objects.filter(date__gte=date_init, date__lte=date_end).order_by('date')
    serializer = UsersLogSerializer(users_log, many=True)
    return HttpResponse(serializer.data, content_type='application/json')


def new_accesslog(request):
    ip_address = get_client_ip(request)
    user = request.user
    details = request.META.get('HTTP_USER_AGENT', '')[:500]
    date = timezone.now().date()

    username = request.GET.get('username')
    if user.is_anonymous and username:
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None

    access_log = AccessLog.objects.filter(
        details=details,
        ip_address=ip_address,
        accessed_date=date
    )
    
    if not access_log.exists():
        AccessLog.objects.create(
            user=user,
            ip_address=ip_address,
            details=details
        )

        if UsersLog.objects.filter(date=date).exists():
            users_log = UsersLog.objects.get(date=date)
            users_log.num_users += 1
            users_log.save()
        else:
            UsersLog.objects.create(
                date=date,
                num_users=1
            )

    elif (
        access_log.exists() and not user.is_anonymous and not access_log.filter(user__pk=user.id).exists()
    ):
        access_log_obj = access_log.first()
        access_log_obj.user = user
        access_log_obj.save()
    
    message = 'Access log registered as anonymous'
    if not user.is_anonymous:
        message = 'Access log registered with user: ' + user.username
    
    return HttpResponse(message, status=200)
