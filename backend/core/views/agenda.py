from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..models import Consulta, Paciente
from ..permissions import medico_required
from ..services import registrar_log

_DIAS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


@login_required
@medico_required
def agenda(request):
    hoy = timezone.localdate()

    if request.method == "POST":
        return _crear_consulta(request, hoy)

    proximas = (
        Consulta.objects
        .filter(estado="programada", fecha_hora__date__gte=hoy)
        .select_related("paciente", "medico")
        .order_by("fecha_hora")
    )
    hoy_citas = proximas.filter(fecha_hora__date=hoy)
    proximas_qs = proximas.filter(fecha_hora__date__gt=hoy)
    proximas_paginator = Paginator(proximas_qs, 10)
    proximas_page = proximas_paginator.get_page(request.GET.get("pp", 1))

    recientes_qs = (
        Consulta.objects
        .filter(estado="realizada")
        .select_related("paciente")
        .order_by("-fecha_hora")
    )
    recientes_paginator = Paginator(recientes_qs, 10)
    recientes_page = recientes_paginator.get_page(request.GET.get("rp", 1))

    semana_inicio = hoy - timedelta(days=hoy.weekday())
    semana_fin = semana_inicio + timedelta(days=6)
    citas_cal = list(
        Consulta.objects
        .filter(fecha_hora__date__gte = semana_inicio, fecha_hora__date__lte = semana_fin)
        .select_related("paciente")
        .order_by("fecha_hora")
    )
    dias_semana = [
        {
            "fecha": semana_inicio + timedelta(days=i),
            "nombre": _DIAS_ES[i],
            "citas": [c for c in citas_cal if timezone.localtime(c.fecha_hora).date() == semana_inicio + timedelta(days=i)],
            "es_hoy": semana_inicio + timedelta(days=i) == hoy,
            "pasado": semana_inicio + timedelta(days=i) < hoy,
        }
        for i in range(7)
    ]

    return render(request, "core/agenda.html", {
        "hoy": hoy,
        "hoy_citas": hoy_citas,
        "proximas_page": proximas_page,
        "recientes_page": recientes_page,
        "pacientes": Paciente.objects.all().order_by("nombre"),
        "tipos": Consulta.TIPOS,
        "hoy": hoy.isoformat(),
        "dias_semana": dias_semana,
        "semana_inicio": semana_inicio,
        "semana_fin": semana_fin,
    })


def _crear_consulta(request, hoy):
    paciente_id = request.POST.get("paciente_id")
    tipo = request.POST.get("tipo", "control")
    fecha_hora_str = request.POST.get("fecha_hora")
    motivo = request.POST.get("motivo", "").strip()

    if not (paciente_id and fecha_hora_str and motivo):
        messages.error(request, "Paciente, fecha/hora y motivo son obligatorios.")
        return redirect("agenda")

    try:
        fecha_hora = datetime.fromisoformat(fecha_hora_str)
    except ValueError:
        messages.error(request, "La fecha y hora de la cita no tienen un formato válido.")
        return redirect("agenda")

    if fecha_hora.date() < hoy:
        messages.error(request, "No se puede agendar una cita en una fecha pasada.")
        return redirect("agenda")

    paciente = get_object_or_404(Paciente, pk=paciente_id)
    Consulta.objects.create(
        paciente = paciente,
        medico = request.user,
        tipo = tipo,
        fecha_hora = fecha_hora,
        motivo = motivo,
    )
    messages.success(request, f"Cita agendada para {paciente.nombre}.")
    return redirect("agenda")


@login_required
@medico_required
def completar_consulta(request, consulta_id):
    if request.method != "POST":
        return redirect("agenda")

    consulta = get_object_or_404(Consulta, pk = consulta_id)
    consulta.diagnostico  = request.POST.get("diagnostico", "").strip()
    consulta.indicaciones = request.POST.get("indicaciones", "").strip()
    proxima_str = request.POST.get("proxima_cita")
    if proxima_str:
        try:
            proxima_date = date.fromisoformat(proxima_str)
        except ValueError:
            messages.error(request, "La fecha de próxima cita no tiene un formato válido.")
            return redirect("agenda")
        if proxima_date < date.today():
            messages.error(request, "La próxima cita no puede programarse en una fecha pasada.")
            return redirect("agenda")
        consulta.proxima_cita = proxima_date
    else:
        consulta.proxima_cita = None
    consulta.estado = "realizada"
    consulta.save()

    registrar_log(
        request,
        accion="completar_consulta",
        paciente=consulta.paciente,
        descripcion=f"Consulta completada: {consulta.get_tipo_display()}",
    )
    messages.success(request, "Consulta registrada correctamente.")
    return redirect("agenda")


@login_required
@medico_required
def cambiar_estado_consulta(request, consulta_id):
    if request.method != "POST":
        return redirect("agenda")

    consulta = get_object_or_404(Consulta, pk = consulta_id)
    nuevo_estado = request.POST.get("estado")
    if nuevo_estado in ("cancelada", "no_asistio", "programada"):
        consulta.estado = nuevo_estado
        consulta.save()
        registrar_log(
            request,
            accion="completar_consulta",
            paciente=consulta.paciente,
            descripcion=f"Estado de consulta cambiado a: {consulta.get_estado_display()}",
        )
    return redirect("agenda")
