from django.contrib import admin
from .models import Paciente, Metrica, Alerta, NotaClinica, PlanCuidado, LogAcceso, PerfilMedico

admin.site.register(Paciente)
admin.site.register(Metrica)
admin.site.register(Alerta)
admin.site.register(NotaClinica)
admin.site.register(PlanCuidado)


admin.site.register(PerfilMedico)


@admin.register(LogAcceso)
class LogAccesoAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'medico', 'paciente', 'get_accion_display', 'ip']
    list_filter = ['accion', 'fecha', 'medico']
    search_fields  = ['medico__username', 'paciente__nombre']
    readonly_fields = ['medico', 'paciente', 'accion', 'descripcion', 'ip', 'fecha']
    ordering = ['-fecha']
