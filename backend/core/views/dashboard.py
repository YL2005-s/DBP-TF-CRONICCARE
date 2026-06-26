from collections import Counter

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render

from ..models import Alerta, Paciente
from ..permissions import medico_required
from ..services import (
    _valor_str,
    construir_lista_pacientes,
    estadisticas_dashboard,
    filtrar_items_dashboard,
)


@login_required
@medico_required
def dashboard_medico(request):
    q = request.GET.get("q", "").strip()
    filtro_enfermedad = request.GET.get("enfermedad", "")
    filtro_estado = request.GET.get("estado", "")

    todos = construir_lista_pacientes()
    stats = estadisticas_dashboard(todos)
    filtrados = filtrar_items_dashboard(todos, q, filtro_enfermedad, filtro_estado)

    paginator = Paginator(filtrados, 10)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    alertas_qs = (
        Alerta.objects
        .filter(resuelta=False, criticidad="critica")
        .select_related("paciente", "metrica")
        .order_by("-fecha")[:3]
    )
    alertas_recientes = [
        {"alerta": a, "valor_str": _valor_str(a.metrica) if a.metrica else None}
        for a in alertas_qs
    ]

    params = request.GET.copy()
    params.pop("page", None)
    filtros_qs = params.urlencode()

    return render(request, "core/dashboard.html", {
        **stats,
        "pacientes_list": page_obj,
        "page_obj": page_obj,
        "q": q,
        "filtro_enfermedad": filtro_enfermedad,
        "filtro_estado": filtro_estado,
        "enfermedades_choices": Paciente.ENFERMEDADES,
        "hay_filtros": bool(q or filtro_enfermedad or filtro_estado),
        "filtros_qs": filtros_qs,
        "alertas_recientes": alertas_recientes,
    })


@login_required
@medico_required
def conteo_alertas_json(request):
    todos = construir_lista_pacientes()
    estables = sum(1 for i in todos if i["estado"] == "estable")
    observacion = sum(1 for i in todos if i["estado"] == "riesgo")
    criticos = sum(1 for i in todos if i["estado"] == "critico")
    criticas = Alerta.objects.filter(resuelta=False, criticidad="critica").count()
    enf_counter = Counter(i["paciente"].get_enfermedad_display() for i in todos)
    return JsonResponse({
        "total": len(todos),
        "estables": estables,
        "observacion": observacion,
        "criticos": criticos,
        "criticas": criticas,
        "enfermedades": [
            {"label": k, "count": v}
            for k, v in sorted(enf_counter.items(), key=lambda x: -x[1])
        ],
    })
