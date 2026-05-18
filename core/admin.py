from django.contrib import admin
from .models import Paciente, Metrica, Alerta, NotaClinica

admin.site.register(Paciente)
admin.site.register(Metrica)
admin.site.register(Alerta)
admin.site.register(NotaClinica)
