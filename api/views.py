from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, BasePermission
from core.models import Paciente, Metrica, Alerta, NotaClinica
from .serializers import PacienteSerializer, MetricaSerializer, AlertaSerializer, NotaClinicaSerializer


class EsMedico(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.groups.filter(name='Medico').exists()
            or request.user.is_superuser
        )


class PacienteViewSet(viewsets.ModelViewSet):
    queryset = Paciente.objects.all()
    serializer_class = PacienteSerializer
    permission_classes = [IsAuthenticated, EsMedico]


class MetricaViewSet(viewsets.ModelViewSet):
    queryset = Metrica.objects.all()
    serializer_class = MetricaSerializer
    permission_classes = [IsAuthenticated, EsMedico]


class AlertaViewSet(viewsets.ModelViewSet):
    queryset = Alerta.objects.all()
    serializer_class = AlertaSerializer
    permission_classes = [IsAuthenticated, EsMedico]


class NotaClinicaViewSet(viewsets.ModelViewSet):
    queryset = NotaClinica.objects.all()
    serializer_class = NotaClinicaSerializer
    permission_classes = [IsAuthenticated, EsMedico]

    def perform_create(self, serializer):
        serializer.save(medico=self.request.user)
