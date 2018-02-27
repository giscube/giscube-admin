from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from .models import Project
from .serializers import ProjectSerializer


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    max_page_size = 500


class ProjectViewSet(viewsets.ModelViewSet):
    lookup_field = 'id'
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    pagination_class = StandardResultsSetPagination
