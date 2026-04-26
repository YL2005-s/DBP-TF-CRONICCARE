from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_medico, name='dashboard'),
    path('paciente/<int:paciente_id>/', views.detalle_paciente, name='detalle_paciente'),
    path('paciente/<int:paciente_id>/pdf/', views.exportar_pdf_paciente, name='exportar_pdf'),
    path('reporte-general/', views.reporte_general_pdf, name='reporte_general'),
    path('simular/<int:paciente_id>/', views.simular_metrica, name='simular'),
    path('alertas/', views.bandeja_alertas, name='alertas'),
    path('registrar/', views.registrar_paciente, name='registrar'),
    path('sin-permiso/', views.sin_permiso, name='sin_permiso'),
]
