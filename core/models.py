from django.db import models
from django.contrib.auth.models import User


class Paciente(models.Model):
    ENFERMEDADES = [
        ('diabetes_t2', 'Diabetes Tipo 2'),
        ('hipertension', 'Hipertensión Arterial'),
        ('asma', 'Asma'),
    ]
    user = models.OneToOneField(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='paciente'
    )
    nombre = models.CharField(max_length=100)
    dni = models.CharField(max_length=8, unique=True)
    enfermedad = models.CharField(max_length=100, choices=ENFERMEDADES)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class Metrica(models.Model):
    TIPOS = [
        ('glucosa',    'Glucosa'),
        ('presion',    'Presión Arterial'),
        ('saturacion', 'Saturación O2'),
        ('frecuencia', 'Frecuencia Cardíaca'),
    ]
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='metricas')
    tipo     = models.CharField(max_length=50, choices=TIPOS)
    valor    = models.FloatField()
    alerta   = models.BooleanField(default=False)
    fecha    = models.DateTimeField(auto_now_add=True)


class Alerta(models.Model):
    CRITICIDAD = [
        ('critica',  'Crítica'),
        ('moderada', 'Moderada'),
        ('leve',     'Leve'),
    ]
    paciente   = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    metrica    = models.ForeignKey(Metrica, on_delete=models.SET_NULL, null=True, related_name='alertas')
    mensaje    = models.TextField()
    criticidad = models.CharField(max_length=20, choices=CRITICIDAD)
    resuelta   = models.BooleanField(default=False)
    fecha      = models.DateTimeField(auto_now_add=True)
