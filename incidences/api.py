from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

from rest_framework import mixins, permissions, viewsets

from .models import Incidence
from .serializers import IncidenceSerializer


class IncidenceViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Incidence.objects.all()
    serializer_class = IncidenceSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request):
        response = super().create(request)

        if settings.DEFAULT_FROM_EMAIL and settings.INCIDENCE_EMAIL:
            try:
                object = response.data
                url = reverse('admin:incidences_incidence_change', args=[object.get('id')])
                url = request.build_absolute_uri(url)
                body = f"Remitent: {object.get('email')}\n\n"
                body += f"Tipus d'incidència: {object.get('title')}\n\n"
                body += f"Descripció: {object.get('description')}\n\n"
                body += f"Enllaç: {url}\n"
                send_mail(
                    f'[{settings.ENVIRONMENT_NAME}] Nova incidència creada',
                    body,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.INCIDENCE_EMAIL],
                    fail_silently=False,
                )
            except Exception as e:
                print('No s\'ha pogut enviar el correu per informar de la creació d\'una nova incidència')
                print(e)

        return response
