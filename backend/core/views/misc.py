from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from ..models import LogAcceso, PerfilMedico
from ..permissions import medico_required
from ..services import registrar_log


@login_required
@medico_required
def auditoria(request):
    qs = LogAcceso.objects.select_related("medico", "paciente").all()

    medico_id = request.GET.get("medico", "")
    accion    = request.GET.get("accion", "")
    desde     = request.GET.get("desde", "")
    hasta     = request.GET.get("hasta", "")

    if medico_id:
        qs = qs.filter(medico_id=medico_id)
    if accion:
        qs = qs.filter(accion=accion)
    if desde:
        qs = qs.filter(fecha__date__gte=desde)
    if hasta:
        qs = qs.filter(fecha__date__lte=hasta)

    paginator = Paginator(qs, 50)
    page      = request.GET.get("page", 1)
    logs      = paginator.get_page(page)

    medicos = User.objects.filter(logs__isnull=False).distinct().order_by("first_name")

    return render(request, "core/auditoria.html", {
        "logs":     logs,
        "medicos":  medicos,
        "acciones": LogAcceso.ACCIONES,
        "filtros": {
            "medico": medico_id,
            "accion": accion,
            "desde":  desde,
            "hasta":  hasta,
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


@login_required
def sin_permiso(request):
    return render(request, "core/sin_permiso.html")
