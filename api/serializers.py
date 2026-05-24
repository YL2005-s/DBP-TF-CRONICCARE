from rest_framework import serializers
from core.models import Paciente, Metrica, Alerta, NotaClinica, PlanCuidado, PerfilMedico


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


class PerfilMedicoSerializer(serializers.ModelSerializer):
    nombre_completo      = serializers.CharField(source='user.get_full_name', read_only=True)
    email                = serializers.CharField(source='user.email', read_only=True)
    especialidad_display = serializers.CharField(source='get_especialidad_display', read_only=True)

    class Meta:
        model  = PerfilMedico
        fields = ['id', 'nombre_completo', 'email',
                  'especialidad', 'especialidad_display',
                  'cmp', 'telefono', 'bio']


class PlanCuidadoSerializer(serializers.ModelSerializer):
    tipo_display         = serializers.CharField(
        source='get_tipo_display', read_only=True)
    tipo_metrica_display = serializers.CharField(
        source='get_tipo_metrica_display', read_only=True)
    frecuencia_display   = serializers.CharField(
        source='get_frecuencia_display', read_only=True)

    class Meta:
        model  = PlanCuidado
        fields = [
            'id', 'paciente', 'tipo', 'tipo_display',
            'tipo_metrica', 'tipo_metrica_display',
            'descripcion', 'hora', 'frecuencia',
            'frecuencia_display', 'activo', 'fecha_inicio'
        ]
