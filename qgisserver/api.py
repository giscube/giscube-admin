import time

from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from giscube.permissions import FixedDjangoModelPermissions

from .models import Project, Service
from .serializers import ProjectSerializer, ServiceSerializer


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    max_page_size = 500


class ProjectViewSet(viewsets.ModelViewSet):
    lookup_field = 'id'
    queryset = Project.objects.all().order_by('pk')
    serializer_class = ProjectSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = (FixedDjangoModelPermissions,)

    @action(methods=['post'], detail=True)
    def publish(self, request, id=None):
        """
        (re)publish a project
        """
        qs = self.get_queryset()
        instance = get_object_or_404(qs, pk=id)

        if instance.service is None:
            instance.service = Service()

        s = instance.service
        s.name = ('%s-%s') % (request.data.get('name'), time.time())
        s.category_id = int(request.data.get('category'))
        s.title = request.data.get('title')
        s.description = request.data.get('description')
        s.keywords = request.data.get('keywords')
        s.visible_on_geoportal = request.data.get('visible_on_geoportal')
        s.project_file = SimpleUploadedFile(instance.name + '.qgs',
                                            instance.data.encode('utf-8'))
        s.save()
        instance.service = s
        instance.save()

        serializer = ProjectSerializer(instance=instance)
        data = serializer.data

        return Response(data)


class ServiceViewSet(viewsets.ModelViewSet):
    lookup_field = 'name'
    queryset = Service.objects.all().order_by('pk')
    serializer_class = ServiceSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = (FixedDjangoModelPermissions,)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
