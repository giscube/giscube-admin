from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

from rest_framework import mixins, permissions, viewsets

from giscube.utils import url_slash_join

from .models import Incidence
from .serializers import IncidenceSerializer


class IncidenceViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Incidence.objects.all()
    serializer_class = IncidenceSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request):
        response = super().create(request)

        if settings.INCIDENCE_EMAIL:
            try:
                object = response.data
                url = reverse('admin:incidences_incidence_change', args=[object.get('id')])
                url = url_slash_join(settings.GISCUBE_URL, url)

                send_mail(
                    'Nova incidència creada',
                    f'S\'ha creat una nova incidència: \n\n{url}',
                    [settings.INCIDENCE_EMAIL],
                    fail_silently=False,
                )
            except Exception as e:
                print('No s\'ha pogut enviar el correu per informar de la creació d\'una nova incidència')
                print(e)

        return response
