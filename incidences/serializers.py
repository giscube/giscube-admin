from django.contrib.auth.models import User

from rest_framework import serializers
from rest_framework_gis.fields import GeometryField

from .models import Incidence


class IncidenceSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_null=True)
    description = serializers.CharField(allow_null=True)
    email = serializers.CharField(allow_null=True)
    geometry = GeometryField()

    class Meta:
        model = Incidence
        fields = '__all__'
