from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from ..models import LogAcceso, Paciente, PerfilMedico
from ..permissions import medico_required
from ..services import registrar_log


class MedicoLoginView(LoginView):
    template_name = "core/login.html"

    def form_valid(self, form):
        user = form.get_user()
        if not (user.groups.filter(name="Medico").exists() or user.is_superuser):
            return render(self.request, self.template_name, {
                "form": form,
                "solo_app": True,
            })
        return super().form_valid(form)


@login_required
@medico_required
def auditoria(request):
    qs = LogAcceso.objects.select_related("medico", "paciente").all()

    medico_id = request.GET.get("medico", "")
    paciente_id = request.GET.get("paciente", "")
    accion = request.GET.get("accion", "")
    desde = request.GET.get("desde", "")
    hasta = request.GET.get("hasta", "")

    if medico_id:
        qs = qs.filter(medico_id=medico_id)
    if paciente_id:
        qs = qs.filter(paciente_id=paciente_id)
    if accion:
        qs = qs.filter(accion=accion)
    if desde:
        qs = qs.filter(fecha__date__gte=desde)
    if hasta:
        qs = qs.filter(fecha__date__lte=hasta)

    paginator = Paginator(qs, 50)
    logs = paginator.get_page(request.GET.get("page", 1))

    medicos = User.objects.filter(logs__isnull=False).distinct().order_by("first_name")
    pacientes = Paciente.objects.filter(logs__isnull=False).distinct().order_by("nombre")

    return render(request, "core/auditoria.html", {
        "logs": logs,
        "medicos": medicos,
        "pacientes": pacientes,
        "acciones": LogAcceso.ACCIONES,
        "filtros": {
            "medico": medico_id,
            "paciente": paciente_id,
            "accion": accion,
            "desde": desde,
            "hasta": hasta,
        },
    })


@login_required
@medico_required
def perfil_medico(request):
    user = request.user
    perfil, _ = PerfilMedico.objects.get_or_create(user = user)

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "actualizar_perfil":
            user.first_name = request.POST.get("first_name", "").strip()
            user.last_name = request.POST.get("last_name", "").strip()
            user.email = request.POST.get("email", "").strip()
            user.save()

            perfil.especialidad = request.POST.get("especialidad", "medicina_general")
            perfil.cmp = request.POST.get("cmp", "").strip()
            perfil.telefono = request.POST.get("telefono", "").strip()
            perfil.bio = request.POST.get("bio", "").strip()
            perfil.save()

            registrar_log(request, accion = "actualizar_perfil", descripcion = "Actualizó su perfil médico")
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect("perfil_medico")

        elif accion == "cambiar_password":
            password_actual = request.POST.get("password_actual")
            password_nueva = request.POST.get("password_nueva")
            password_confirm = request.POST.get("password_confirm")

            if not user.check_password(password_actual):
                messages.error(request, "La contraseña actual es incorrecta.")
            elif password_nueva != password_confirm:
                messages.error(request, "Las contraseñas nuevas no coinciden.")
            elif len(password_nueva) < 8:
                messages.error(request, "La contraseña debe tener al menos 8 caracteres.")
            else:
                user.set_password(password_nueva)
                user.save()
                messages.success(request, "Contraseña actualizada. Por favor inicia sesión nuevamente.")
                return redirect("login")

        return redirect("perfil_medico")

    return render(request, "core/perfil_medico.html", {"perfil": perfil, "user": user})


_FAQS = [
    (
        "¿Cómo obtiene el paciente la contraseña para la app móvil?",
        "Al registrar un paciente el sistema genera automáticamente una contraseña temporal. "
        "Esta aparece en pantalla solo una vez al momento del registro. Anótela y entréguela al paciente. "
        "Si se pierde, un administrador puede resetearla desde el panel de administración.",
    ),
    (
        "¿Qué pasa si un paciente registra una métrica con un valor incorrecto?",
        "La métrica queda guardada en el historial y puede consultarse en el perfil del paciente. "
        "Si generó una alerta errónea, puede resolverla manualmente desde la bandeja de alertas. "
        "No es posible eliminar métricas desde el portal web; solo un administrador puede hacerlo desde el panel de administración.",
    ),
    (
        "¿Cada cuánto tiempo se actualizan las alertas en el dashboard?",
        "El dashboard refresca el conteo de alertas cada 10 segundos de forma automática sin recargar la página. "
        "El listado completo de pacientes se actualiza al recargar manualmente o al aplicar un filtro.",
    ),
    (
        "¿Puedo configurar umbrales distintos para cada paciente?",
        "Sí. En la Ficha Médica de cada paciente existe una sección de umbrales personalizados. "
        "Puede definir valores mínimos y máximos para glucosa, presión sistólica, presión diastólica, saturación y frecuencia cardíaca. "
        "Si no se configura un umbral personalizado, el sistema usa los valores estándar según la enfermedad crónica del paciente. "
        "Al guardar umbrales nuevos, el historial completo se revalúa automáticamente.",
    ),
    (
        "¿Cómo exporto las métricas de un paciente?",
        "En el perfil del paciente, use el botón Exportar CSV. "
        "Se descarga un archivo .csv con todas las métricas ordenadas por fecha, incluyendo tipo, valor, valor diastólica y si generó alerta.",
    ),
    (
        "¿Qué información registra la auditoría?",
        "La auditoría registra cada acción significativa: ver un paciente, agregar notas o planes, resolver alertas, exportar CSV, "
        "registrar un paciente nuevo y cambios de perfil. Incluye quién realizó la acción, a qué paciente afecta, la IP de origen y la fecha exacta. "
        "Se puede filtrar por médico, paciente, tipo de acción y rango de fechas.",
    ),
    (
        "¿Por qué un paciente aparece como 'Crítico' si ya resolví sus alertas?",
        "El estado se recalcula en tiempo real al cargar el dashboard. Si resolvió la alerta hace menos de 24 horas, "
        "es posible que aún haya métricas con alerta activa que no fueron evaluadas. "
        "Vaya al perfil del paciente y abra la ficha médica: al guardar los umbrales (sin cambiarlos) se fuerza una re-evaluación completa del historial.",
    ),
    (
        "¿Los médicos pueden acceder a la app móvil?",
        "No. La app móvil es exclusiva para pacientes. Si un médico intenta iniciar sesión desde la app, "
        "recibirá un mensaje indicando que debe usar el portal web. "
        "El portal web (esta plataforma) es el canal exclusivo para el equipo médico.",
    ),
]


@login_required
@medico_required
def ayuda(request):
    return render(request, "core/ayuda.html", {"faqs": _FAQS})


@login_required
def sin_permiso(request):
    return render(request, "core/sin_permiso.html")
