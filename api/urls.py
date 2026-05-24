from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('pacientes', views.PacienteViewSet)
router.register('metricas', views.MetricaViewSet)
router.register('alertas', views.AlertaViewSet)
router.register('notas', views.NotaClinicaViewSet)
router.register(r'planes', views.PlanCuidadoViewSet, basename='planes')

urlpatterns = router.urls
