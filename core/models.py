from django.db import models
from django.contrib.auth.models import User

class Paciente(models.Model):
    nombre = models.CharField(max_length=100)
    dni = models.CharField(max_length=8, unique=True)
    enfermedad = models.CharField(max_length=100)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

class Metrica(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='metricas')
    tipo = models.CharField(max_length=50)
    valor = models.CharField(max_length=20)
    alerta = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

class Alerta(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    mensaje = models.TextField()
    criticidad = models.CharField(max_length=20)
    resuelta = models.BooleanField(default=False)