from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_medico, name='dashboard'),
    path('dashboard/conteo-alertas/', views.conteo_alertas_json, name='conteo_alertas_json'),

    path('registrar/', views.registrar_paciente, name='registrar'),
    path('paciente/<int:paciente_id>/', views.detalle_paciente, name='detalle_paciente'),
    path('paciente/<int:paciente_id>/ficha/', views.ficha_medica,          name='ficha_medica'),

    path('agenda/', views.agenda, name='agenda'),
    path('consulta/<int:consulta_id>/completar/', views.completar_consulta, name='completar_consulta'),
    path('consulta/<int:consulta_id>/estado/', views.cambiar_estado_consulta, name='cambiar_estado_consulta'),

    path('alertas/', views.bandeja_alertas, name='alertas'),
    path('alertas/<int:alerta_id>/resolver/', views.resolver_alerta, name='resolver_alerta'),

    path('paciente/<int:paciente_id>/pdf/', views.exportar_pdf_paciente, name='exportar_pdf'),
    path('reporte-general/', views.reporte_general_pdf, name='reporte_general'),

    path('auditoria/', views.auditoria, name='auditoria'),
    path('perfil/', views.perfil_medico, name='perfil_medico'),
    path('sin-permiso/', views.sin_permiso, name='sin_permiso'),
]
