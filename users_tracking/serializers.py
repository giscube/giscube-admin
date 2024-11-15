from rest_framework import serializers

from .models import LayerRegister, ToolRegister


class LayerRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = LayerRegister
        fields = '__all__'


class ToolRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolRegister
        fields = '__all__'
