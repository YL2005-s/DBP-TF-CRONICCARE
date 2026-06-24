from django.contrib import admin
from .models import Paciente, Metrica, Alerta, NotaClinica, PlanCuidado, LogAcceso, PerfilMedico, FichaMedica, Prescripcion, UmbralPersonalizado, Consulta

admin.site.register(Paciente)
admin.site.register(Metrica)
admin.site.register(Alerta)
admin.site.register(NotaClinica)
admin.site.register(PlanCuidado)
admin.site.register(PerfilMedico)


@admin.register(FichaMedica)
class FichaMedicaAdmin(admin.ModelAdmin):
    list_display = ['paciente', 'tipo_sangre', 'peso_kg', 'talla_cm', 'fecha_actualizacion']
    search_fields = ['paciente__nombre', 'paciente__dni']
    readonly_fields = ['fecha_actualizacion']


@admin.register(Prescripcion)
class PrescripcionAdmin(admin.ModelAdmin):
    list_display = ['medicamento', 'dosis', 'paciente', 'medico', 'fecha_inicio', 'fecha_fin', 'activa']
    list_filter = ['activa', 'via', 'frecuencia']
    search_fields = ['medicamento', 'paciente__nombre', 'medico__username']
    readonly_fields = ['fecha_registro']


@admin.register(UmbralPersonalizado)
class UmbralPersonalizadoAdmin(admin.ModelAdmin):
    list_display = ['paciente', 'tipo_metrica', 'valor_min', 'valor_max']
    list_filter = ['tipo_metrica']
    search_fields = ['paciente__nombre']


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ['paciente', 'medico', 'tipo', 'estado', 'fecha_hora']
    list_filter = ['tipo', 'estado']
    search_fields = ['paciente__nombre', 'medico__username', 'motivo']
    readonly_fields = ['fecha_registro']


@admin.register(LogAcceso)
class LogAccesoAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'medico', 'paciente', 'get_accion_display', 'ip']
    list_filter = ['accion', 'fecha', 'medico']
    search_fields  = ['medico__username', 'paciente__nombre']
    readonly_fields = ['medico', 'paciente', 'accion', 'descripcion', 'ip', 'fecha']
    ordering = ['-fecha']
