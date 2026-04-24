"""
URL configuration for cronic project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', views.dashboard_medico, name='dashboard'),
    path('paciente/<int:paciente_id>/', views.detalle_paciente, name='detalle_paciente'),
    path('paciente/<int:paciente_id>/pdf/', views.exportar_pdf_paciente, name='exportar_pdf'),
    path('reporte-general/', views.reporte_general_pdf, name='reporte_general'),
    path('simular/<int:paciente_id>/', views.simular_metrica, name='simular'),
    path('alertas/', views.bandeja_alertas, name='alertas'),
    path('registrar/', views.registrar_paciente, name='registrar'),
]