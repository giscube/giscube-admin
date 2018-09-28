from django.core.validators import FileExtensionValidator
from rest_framework import serializers

from .models import Project, Service


class ServiceSerializer(serializers.ModelSerializer):
    project_file = serializers.FileField(
        validators=[FileExtensionValidator(allowed_extensions=['qgs'])]
    )

    class Meta:
        model = Service
        fields = ('id', 'name', 'title', 'description', 'keywords', 'active',
                  'visible_on_geoportal', 'category', 'project_file')


class ProjectSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ('id', 'name', 'data', 'service')
