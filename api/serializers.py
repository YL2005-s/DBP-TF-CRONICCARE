from rest_framework import serializers
from core.models import Paciente, Metrica, Alerta, NotaClinica


class MetricaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metrica
        fields = '__all__'


class AlertaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerta
        fields = '__all__'


class PacienteSerializer(serializers.ModelSerializer):
    enfermedad_display = serializers.CharField(
        source='get_enfermedad_display', read_only=True
    )

    class Meta:
        model = Paciente
        fields = ['id', 'nombre', 'dni', 'enfermedad',
                  'enfermedad_display', 'fecha_registro']


class NotaClinicaSerializer(serializers.ModelSerializer):
    medico_nombre = serializers.CharField(
        source='medico.get_full_name', read_only=True
    )

    class Meta:
        model = NotaClinica
        fields = ['id', 'paciente', 'medico_nombre', 'texto', 'fecha']
