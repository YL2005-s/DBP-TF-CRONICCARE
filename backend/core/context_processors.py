from core.models import Alerta


def alertas_pendientes(request):
    if not request.user.is_authenticated:
        return {
            'total_alertas_pendientes': 0,
            'alertas_recientes': [],
        }

    alertas = list(Alerta.objects.filter(
        resuelta=False,
        criticidad='critica',
    ).select_related('paciente', 'metrica').order_by('-fecha'))

    alertas_data = [
        {
            'alerta': alerta,
            'valor_str': f"{float(alerta.metrica.valor):.1f}" if alerta.metrica else None,
        }
        for alerta in alertas[:3]
    ]

    return {
        'total_alertas_pendientes': len(alertas),
        'alertas_recientes': alertas_data,
    }
