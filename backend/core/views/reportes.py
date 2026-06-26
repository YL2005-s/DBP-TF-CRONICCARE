import re

from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.utils import timezone
from xhtml2pdf import pisa

from ..models import FichaMedica, Metrica, Paciente, PerfilMedico
from ..permissions import medico_required
from ..services import registrar_log, ultimas_metricas_por_tipo


@login_required
@medico_required
def exportar_pdf_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    metricas = paciente.metricas.all().order_by("-fecha")

    registrar_log(
        request,
        accion = "generar_pdf",
        paciente = paciente,
        descripcion = f"PDF individual generado para {paciente.nombre}",
    )

    context = {
        "paciente": paciente,
        "metricas": metricas,
        "ultimas_por_tipo": ultimas_metricas_por_tipo(paciente),
    }

    nombre_slug = re.sub(r"[^a-z0-9]+", "_", paciente.nombre.lower().strip()).strip("_")
    filename = f"reporte_croniccare_{nombre_slug}_{paciente.dni}.pdf"

    return _render_pdf("core/reportes/reporte_pdf.html", context, filename)


@login_required
@medico_required
def reporte_general_pdf(request):
    registrar_log(
        request,
        accion = "generar_pdf",
        descripcion = "Reporte general PDF generado",
    )

    pacientes_en_alerta = (
        Paciente.objects
        .filter(alertas__resuelta = False, alertas__criticidad = "critica")
        .distinct()
        .count()
    )
    pacientes = Paciente.objects.prefetch_related(
        Prefetch(
            "metricas",
            queryset=Metrica.objects.order_by("-fecha"),
            to_attr="metricas_list",
        )
    )
    context = {
        "pacientes": pacientes,
        "pacientes_en_alerta": pacientes_en_alerta,
    }

    fecha_str = timezone.localdate().strftime("%Y%m%d")
    return _render_pdf(
        "core/reportes/reporte_general_pdf.html",
        context,
        f"reporte_croniccare_general_{fecha_str}.pdf",
    )


@login_required
@medico_required
def exportar_ficha_pdf(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    ficha, _ = FichaMedica.objects.get_or_create(paciente=paciente)
    umbrales = {u.tipo_metrica: u for u in paciente.umbrales.all()}

    medico_perfil = None
    try:
        medico_perfil = request.user.perfil_medico
    except PerfilMedico.DoesNotExist:
        pass

    registrar_log(
        request,
        accion="generar_pdf",
        paciente=paciente,
        descripcion=f"Ficha médica PDF generada para {paciente.nombre}",
    )

    context = {
        "paciente": paciente,
        "ficha": ficha,
        "prescripciones_activas": paciente.prescripciones.filter(activa=True).select_related("medico"),
        "umbrales": umbrales,
        "medico": request.user,
        "medico_perfil": medico_perfil,
    }

    nombre_slug = re.sub(r"[^a-z0-9]+", "_", paciente.nombre.lower().strip()).strip("_")
    filename = f"ficha_medica_{nombre_slug}_{paciente.dni}.pdf"

    return _render_pdf("core/reportes/ficha_medica_pdf.html", context, filename)


def _render_pdf(template_path, context, filename):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    html = get_template(template_path).render(context)
    status = pisa.CreatePDF(html, dest=response)

    if status.err:
        return HttpResponse("Error al generar el reporte", status=500)
    return response
