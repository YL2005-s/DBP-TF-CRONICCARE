from django.contrib import admin
from .models import Paciente, Metrica, Alerta

admin.site.register(Paciente)
admin.site.register(Metrica)
admin.site.register(Alerta)
