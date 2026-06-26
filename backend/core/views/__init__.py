from .dashboard import dashboard_medico, conteo_alertas_json
from .pacientes import detalle_paciente, registrar_paciente, ficha_medica, exportar_csv_metricas
from .alertas import bandeja_alertas, resolver_alerta
from .agenda import agenda, completar_consulta, cambiar_estado_consulta
from .reportes import exportar_pdf_paciente, reporte_general_pdf
from .misc import auditoria, perfil_medico, sin_permiso

__all__ = [
    "dashboard_medico",
    "conteo_alertas_json",
    "detalle_paciente",
    "registrar_paciente",
    "ficha_medica",
    "exportar_csv_metricas",
    "bandeja_alertas",
    "resolver_alerta",
    "agenda",
    "completar_consulta",
    "cambiar_estado_consulta",
    "exportar_pdf_paciente",
    "reporte_general_pdf",
    "auditoria",
    "perfil_medico",
    "sin_permiso",
]
