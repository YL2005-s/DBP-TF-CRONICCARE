from rest_framework import serializers
from core.models import Paciente, Metrica, Alerta


class MetricaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metrica
        fields = '__all__'


class AlertaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerta
        fields = '__all__'


class PacienteSerializer(serializers.ModelSerializer):
    metricas = MetricaSerializer(many=True, read_only=True)

    class Meta:
        model = Paciente
        fields = '__all__'
