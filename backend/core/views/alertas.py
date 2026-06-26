import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from ..models import Alerta, NotaClinica, Paciente
from ..permissions import medico_required
from ..services import formatear_alertas, registrar_log


@login_required
@medico_required
def bandeja_alertas(request):
    filtro_criticidad = request.GET.get("criticidad", "")
    filtro_enfermedad = request.GET.get("enfermedad", "")

    alertas_qs = (
        Alerta.objects
        .filter(resuelta=False)
        .select_related("paciente", "metrica")
        .order_by("-fecha")
    )
    if filtro_criticidad:
        alertas_qs = alertas_qs.filter(criticidad = filtro_criticidad)
    if filtro_enfermedad:
        alertas_qs = alertas_qs.filter(paciente__enfermedad = filtro_enfermedad)

    return render(request, "core/alertas.html", {
        "alertas": formatear_alertas(alertas_qs),
        "filtro_criticidad": filtro_criticidad,
        "filtro_enfermedad": filtro_enfermedad,
        "enfermedades_choices": Paciente.ENFERMEDADES,
        "criticidad_choices": Alerta.CRITICIDAD,
    })


@login_required
@medico_required
def resolver_alerta(request, alerta_id):
    if request.method != "POST":
        return redirect("alertas")

    alerta = get_object_or_404(Alerta, pk = alerta_id)
    alerta.resuelta = True
    alerta.save()

    nota_texto = ""
    if request.headers.get("Content-Type") == "application/json":
        try:
            nota_texto = json.loads(request.body).get("nota", "").strip()
        except Exception:
            pass

    if nota_texto:
        NotaClinica.objects.create(
            paciente = alerta.paciente,
            medico = request.user,
            texto = f"[Alerta resuelta] {nota_texto}",
        )

    registrar_log(
        request,
        accion = "marcar_alerta",
        paciente = alerta.paciente,
        descripcion = f"Alerta ID {alerta_id} marcada como resuelta",
    )

    if request.headers.get("Content-Type") == "application/json":
        return JsonResponse({"ok": True})
    return redirect("alertas")
