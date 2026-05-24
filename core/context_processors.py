from core.models import Alerta


def alertas_pendientes(request):
    if not request.user.is_authenticated:
        return {
            'total_alertas_pendientes': 0,
            'alertas_recientes': [],
        }

    alertas = Alerta.objects.filter(
        resuelta=False,
        criticidad='critica',
    ).select_related('paciente', 'metrica').order_by('-fecha')

    alertas_data = []
    for alerta in alertas[:3]:
        alertas_data.append({
            'alerta': alerta,
            'valor_str': f"{float(alerta.metrica.valor):.1f}" if alerta.metrica else None,
        })

    return {
        'total_alertas_pendientes': alertas.count(),
        'alertas_recientes': alertas_data,
    }
