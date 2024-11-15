from rest_framework import mixins, permissions, viewsets

from .models import LayerRegister, ToolRegister
from .serializers import LayerRegisterSerializer, ToolRegisterSerializer


class LayerRegisterViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [permissions.IsAuthenticated]
    queryset = LayerRegister.objects.all()
    serializer_class = LayerRegisterSerializer


class ToolRegisterViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [permissions.IsAuthenticated]
    queryset = ToolRegister.objects.all()
    serializer_class = ToolRegisterSerializer
