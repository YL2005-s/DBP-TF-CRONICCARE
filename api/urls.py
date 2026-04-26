from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('pacientes', views.PacienteViewSet)
router.register('metricas', views.MetricaViewSet)
router.register('alertas', views.AlertaViewSet)

urlpatterns = router.urls
