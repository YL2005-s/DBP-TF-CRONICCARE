from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from core.models import Paciente, Metrica, Alerta
from .serializers import PacienteSerializer, MetricaSerializer, AlertaSerializer


class PacienteViewSet(viewsets.ModelViewSet):
    queryset = Paciente.objects.all()
    serializer_class = PacienteSerializer
    permission_classes = [IsAuthenticated]


class MetricaViewSet(viewsets.ModelViewSet):
    queryset = Metrica.objects.all()
    serializer_class = MetricaSerializer
    permission_classes = [IsAuthenticated]


class AlertaViewSet(viewsets.ModelViewSet):
    queryset = Alerta.objects.all()
    serializer_class = AlertaSerializer
    permission_classes = [IsAuthenticated]
