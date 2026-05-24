from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'pacientes', views.PacienteViewSet)
router.register(r'metricas', views.MetricaViewSet)
router.register(r'alertas', views.AlertaViewSet)
router.register(r'notas', views.NotaClinicaViewSet)
router.register(r'planes', views.PlanCuidadoViewSet, basename='planes')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', views.login_token, name='api_login'),
    path('mis-metricas/', views.mis_metricas, name='mis_metricas'),
    path('registrar-metrica/', views.registrar_metrica_movil, name='registrar_metrica_movil'),
    path('mi-plan/', views.mi_plan_cuidados, name='mi_plan'),
]
