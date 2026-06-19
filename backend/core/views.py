import re
import secrets
import random
from datetime import timedelta, date
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import Paciente, Metrica, Alerta, NotaClinica, PlanCuidado, LogAcceso, PerfilMedico, FichaMedica, Prescripcion, UmbralPersonalizado, Consulta


def es_medico(user):
    return user.groups.filter(name='Medico').exists() or user.is_superuser


medico_required = user_passes_test(es_medico, login_url='sin_permiso')


def calcular_estado_paciente(paciente):
    ahora = timezone.now()
    ultimas_24h = ahora - timedelta(hours=24)
    ultimas_48h = ahora - timedelta(hours=48)

    alerta_critica = Alerta.objects.filter(
        paciente=paciente,
        resuelta=False,
        criticidad='critica',
        fecha__gte=ultimas_24h,
    ).exists()

    if alerta_critica:
        return 'critico'

    metricas_alerta = Metrica.objects.filter(
        paciente=paciente,
        alerta=True,
        fecha__gte=ultimas_48h,
    ).count()

    if metricas_alerta >= 2:
        return 'riesgo'

    return 'estable'


def registrar_log(request, accion, paciente=None, descripcion=''):
    ip = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip:
        ip = ip.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    LogAcceso.objects.create(
        medico=request.user,
        paciente=paciente,
        accion=accion,
        descripcion=descripcion,
        ip=ip,
    )


@login_required
@medico_required
def dashboard_medico(request):
    pacientes = Paciente.objects.all()
    alertas_criticas = Alerta.objects.filter(resuelta=False, criticidad='critica').count()

    pacientes_list = []
    for p in pacientes:
        estado = calcular_estado_paciente(p)
        pacientes_list.append({
            'paciente': p,
            'estado': estado,
            'ultima_metrica': p.metricas.last(),
        })

    pacientes_seguros = sum(1 for item in pacientes_list if item['estado'] == 'estable')

    return render(request, 'core/dashboard.html', {
        'pacientes': pacientes,
        'pacientes_list': pacientes_list,
        'alertas_count': alertas_criticas,
        'pacientes_seguros': pacientes_seguros,
    })


@login_required
@medico_required
def detalle_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'agregar_nota':
            texto = request.POST.get('nota_texto', '').strip()
            if texto:
                NotaClinica.objects.create(
                    paciente=paciente,
                    medico=request.user,
                    texto=texto,
                )
                registrar_log(
                    request,
                    accion='agregar_nota',
                    paciente=paciente,
                    descripcion=f"Nota: {texto[:50]}...",
                )
                messages.success(request, 'Nota clínica agregada correctamente.')

        elif accion == 'agregar_plan':
            tipo = request.POST.get('plan_tipo')
            tipo_metrica = request.POST.get('plan_tipo_metrica') or None
            descripcion = request.POST.get('plan_descripcion', '').strip()
            hora = request.POST.get('plan_hora')
            frecuencia = request.POST.get('plan_frecuencia', 'diario')

            if descripcion and hora:
                PlanCuidado.objects.create(
                    paciente=paciente,
                    tipo=tipo,
                    tipo_metrica=tipo_metrica if tipo == 'metrica' else None,
                    descripcion=descripcion,
                    hora=hora,
                    frecuencia=frecuencia,
                    creado_por=request.user,
                )
                registrar_log(
                    request,
                    accion='agregar_plan',
                    paciente=paciente,
                    descripcion=f"Plan: {descripcion}",
                )
                messages.success(request, 'Ítem agregado al plan de cuidados.')

        elif accion == 'desactivar_plan':
            plan_id = request.POST.get('plan_id')
            PlanCuidado.objects.filter(
                pk=plan_id,
                paciente=paciente
            ).update(activo=False)
            registrar_log(
                request,
                accion='eliminar_plan',
                paciente=paciente,
                descripcion=f"Plan eliminado ID: {plan_id}",
            )
            messages.success(request, 'Ítem eliminado del plan.')

        else:
            texto = request.POST.get('nota_texto', '').strip()
            if texto:
                NotaClinica.objects.create(
                    paciente=paciente,
                    medico=request.user,
                    texto=texto,
                )
                registrar_log(
                    request,
                    accion='agregar_nota',
                    paciente=paciente,
                    descripcion=f"Nota: {texto[:50]}...",
                )
                messages.success(request, 'Nota clínica agregada correctamente.')

        return redirect('detalle_paciente', paciente_id=paciente_id)

    registrar_log(
        request,
        accion='ver_paciente',
        paciente=paciente,
        descripcion=f"Accedió a la ficha de {paciente.nombre}",
    )

    estado_paciente = calcular_estado_paciente(paciente)
    metricas = paciente.metricas.all().order_by('-fecha')
    notas = paciente.notas.select_related('medico').all()
    planes = paciente.planes.filter(activo=True)

    ultima_metrica   = metricas.first()
    ultima_valor_str = f"{float(ultima_metrica.valor):.1f}" if ultima_metrica else None

    metricas_formateadas = []
    for m in metricas:
        metricas_formateadas.append({
            'metrica': m,
            'valor_str': f"{float(m.valor):.1f}",
            'fecha_str': m.fecha.strftime('%d/%m/%y %H:%M'),
        })

    periodo = request.GET.get('periodo', '10')
    ahora = timezone.now()

    if periodo == 'semana':
        desde = ahora - timedelta(days=7)
        metricas_grafica = paciente.metricas.filter(fecha__gte=desde).order_by('fecha')
        periodo_label = 'Últimos 7 días'
    elif periodo == 'mes':
        desde = ahora - timedelta(days=30)
        metricas_grafica = paciente.metricas.filter(fecha__gte=desde).order_by('fecha')
        periodo_label = 'Últimos 30 días'
    else:
        periodo = '10'
        metricas_grafica = list(paciente.metricas.order_by('-fecha')[:10])[::-1]
        periodo_label = 'Últimas 10 mediciones'

    labels  = [m.fecha.strftime('%d/%m %H:%M') for m in metricas_grafica]
    valores = [float(m.valor) for m in metricas_grafica]
    alertas = [m.alerta for m in metricas_grafica]

    return render(request, 'core/detalle_paciente.html', {
        'paciente': paciente,
        'estado_paciente': estado_paciente,
        'metricas': metricas,
        'metricas_formateadas': metricas_formateadas,
        'ultima_valor_str': ultima_valor_str,
        'notas': notas,
        'planes': planes,
        'chart_labels':  labels,
        'chart_valores': valores,
        'chart_alertas': alertas,
        'periodo': periodo,
        'periodo_label': periodo_label,
        'total_grafica': len(labels),
    })


@login_required
@medico_required
def exportar_pdf_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    metricas = paciente.metricas.all().order_by('-fecha')

    registrar_log(
        request,
        accion='generar_pdf',
        paciente=paciente,
        descripcion=f"PDF individual generado para {paciente.nombre}",
    )

    template_path = 'core/reportes/reporte_pdf.html'
    context = {'paciente': paciente, 'metricas': metricas}

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Reporte_{paciente.dni}.pdf"'

    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Error al generar el reporte', status=500)
    return response


@login_required
@medico_required
def reporte_general_pdf(request):
    registrar_log(
        request,
        accion='generar_pdf',
        descripcion="Reporte general PDF generado",
    )
    pacientes = Paciente.objects.all()
    template_path = 'core/reportes/reporte_general_pdf.html'
    context = {'pacientes': pacientes}

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Reporte_General_CronicCare.pdf"'

    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Error al generar el reporte', status=500)
    return response


@login_required
def simular_metrica(request, paciente_id):
    if request.method != 'POST':
        return redirect('dashboard')
    paciente = get_object_or_404(Paciente, id=paciente_id)

    if paciente.enfermedad == 'diabetes_t2':
        tipo = 'glucosa'
        valor_simulado = round(random.uniform(80, 200), 1)
        umbral_alerta = 126
        es_alerta = valor_simulado > umbral_alerta
        unidad = 'mg/dL'
        nombre_metrica = 'Glucosa'
    elif paciente.enfermedad == 'hipertension':
        tipo = 'presion'
        valor_simulado = round(random.uniform(100, 180), 1)
        umbral_alerta = 140
        es_alerta = valor_simulado > umbral_alerta
        unidad = 'mmHg'
        nombre_metrica = 'Presión arterial'
    else:  # asma
        tipo = 'saturacion'
        valor_simulado = round(random.uniform(85, 100), 1)
        umbral_alerta = 90
        es_alerta = valor_simulado < umbral_alerta
        unidad = '%'
        nombre_metrica = 'Saturación O2'

    metrica = Metrica.objects.create(
        paciente=paciente,
        tipo=tipo,
        valor=valor_simulado,
        alerta=es_alerta,
    )

    if es_alerta:
        Alerta.objects.create(
            paciente=paciente,
            metrica=metrica,
            mensaje=f'{nombre_metrica} en {valor_simulado:.1f} {unidad} — fuera del rango seguro (umbral: {umbral_alerta} {unidad})',
            criticidad='critica',
        )

    registrar_log(
        request,
        accion='simular_metrica',
        paciente=paciente,
        descripcion=f"Métrica simulada: {tipo} = {valor_simulado}",
    )

    return redirect('dashboard')


@login_required
@medico_required
def bandeja_alertas(request):
    alertas_raw = Alerta.objects.filter(
        resuelta=False
    ).select_related('paciente', 'metrica').order_by('-fecha')

    alertas_formateadas = []
    for a in alertas_raw:
        valor_str = f"{float(a.metrica.valor):.1f}" if a.metrica else None
        alertas_formateadas.append({
            'alerta': a,
            'valor_str': valor_str,
            'fecha_str': a.fecha.strftime('%d/%m %H:%M'),
        })

    return render(request, 'core/alertas.html', {'alertas': alertas_formateadas})


@login_required
@medico_required
def resolver_alerta(request, alerta_id):
    if request.method == 'POST':
        alerta = get_object_or_404(Alerta, pk=alerta_id)
        alerta.resuelta = True
        alerta.save()
        registrar_log(
            request,
            accion='marcar_alerta',
            paciente=alerta.paciente,
            descripcion=f"Alerta ID {alerta_id} marcada como resuelta",
        )
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'ok': True})
    return redirect('alertas')


@login_required
@medico_required
def conteo_alertas_json(request):
    total = Alerta.objects.filter(resuelta=False, criticidad='critica').count()
    return JsonResponse({'criticas': total})


@login_required
@medico_required
def registrar_paciente(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        dni = request.POST.get('dni')
        enfermedad = request.POST.get('enfermedad')

        if not nombre or not dni:
            messages.error(request, 'Nombre y DNI son obligatorios.')
            return render(request, 'core/registro.html')
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$', nombre):
            messages.error(request,
                'El nombre solo puede contener letras y espacios, sin caracteres especiales.')
            return render(request, 'core/registro.html')
        if not dni.isdigit() or len(dni) != 8:
            messages.error(request, 'El DNI debe contener exactamente 8 dígitos numéricos.')
            return render(request, 'core/registro.html')

        if Paciente.objects.filter(dni=dni).exists():
            messages.error(request, f"El DNI {dni} ya está registrado en el sistema.")
            return render(request, 'core/registro.html')

        if User.objects.filter(username=dni).exists():
            messages.error(request, f"Ya existe un usuario con el DNI {dni}.")
            return render(request, 'core/registro.html')

        password_temp = secrets.token_urlsafe(8)
        user = User.objects.create_user(username=dni, password=password_temp)

        grupo_paciente, _ = Group.objects.get_or_create(name='Paciente')
        user.groups.add(grupo_paciente)

        fecha_nac = request.POST.get('fecha_nacimiento')
        telefono = request.POST.get('telefono', '').strip()
        paciente = Paciente.objects.create(
            user=user,
            nombre=nombre,
            dni=dni,
            enfermedad=enfermedad,
            fecha_nacimiento=fecha_nac if fecha_nac else None,
            telefono=telefono,
        )
        FichaMedica.objects.create(paciente=paciente)

        registrar_log(
            request,
            accion='registrar_paciente',
            paciente=paciente,
            descripcion=f"Paciente {nombre} registrado con DNI {dni}",
        )

        return render(request, 'core/registro.html', {
            'registro_exitoso': True,
            'credenciales': {'usuario': dni, 'password': password_temp},
            'paciente': paciente,
        })

    return render(request, 'core/registro.html')


@login_required
def sin_permiso(request):
    return render(request, 'core/sin_permiso.html')


@login_required
@medico_required
def auditoria(request):
    logs = LogAcceso.objects.select_related('medico', 'paciente').all()[:100]
    return render(request, 'core/auditoria.html', {'logs': logs})


@login_required
@medico_required
def perfil_medico(request):
    user = request.user
    perfil, _ = PerfilMedico.objects.get_or_create(user=user)

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'actualizar_perfil':
            user.first_name = request.POST.get('first_name', '').strip()
            user.last_name  = request.POST.get('last_name', '').strip()
            user.email      = request.POST.get('email', '').strip()
            user.save()

            perfil.especialidad = request.POST.get('especialidad', 'medicina_general')
            perfil.cmp          = request.POST.get('cmp', '').strip()
            perfil.telefono     = request.POST.get('telefono', '').strip()
            perfil.bio          = request.POST.get('bio', '').strip()
            perfil.save()

            registrar_log(
                request,
                accion='ver_paciente',
                descripcion='Actualizó su perfil médico',
            )
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('perfil_medico')

        elif accion == 'cambiar_password':
            password_actual  = request.POST.get('password_actual')
            password_nueva   = request.POST.get('password_nueva')
            password_confirm = request.POST.get('password_confirm')

            if not user.check_password(password_actual):
                messages.error(request, 'La contraseña actual es incorrecta.')
            elif password_nueva != password_confirm:
                messages.error(request, 'Las contraseñas nuevas no coinciden.')
            elif len(password_nueva) < 8:
                messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
            else:
                user.set_password(password_nueva)
                user.save()
                messages.success(request, 'Contraseña actualizada. Por favor inicia sesión nuevamente.')
                return redirect('login')

        return redirect('perfil_medico')

    return render(request, 'core/perfil_medico.html', {
        'perfil': perfil,
        'user': user,
    })


@login_required
@medico_required
def ficha_medica(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    ficha, _ = FichaMedica.objects.get_or_create(paciente=paciente)
    umbrales = {u.tipo_metrica: u for u in paciente.umbrales.all()}

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'actualizar_ficha':
            fecha_nac = request.POST.get('fecha_nacimiento')
            paciente.fecha_nacimiento = fecha_nac if fecha_nac else None
            paciente.telefono = request.POST.get('telefono', '').strip()
            paciente.save()

            ficha.tipo_sangre               = request.POST.get('tipo_sangre', '')
            peso = request.POST.get('peso_kg')
            talla = request.POST.get('talla_cm')
            ficha.peso_kg                   = float(peso) if peso else None
            ficha.talla_cm                  = float(talla) if talla else None
            ficha.alergias                  = request.POST.get('alergias', '').strip()
            ficha.cirugias_previas          = request.POST.get('cirugias_previas', '').strip()
            ficha.hospitalizaciones         = request.POST.get('hospitalizaciones', '').strip()
            ficha.antecedentes_familiares   = request.POST.get('antecedentes_familiares', '').strip()
            ficha.historia_enfermedad       = request.POST.get('historia_enfermedad', '').strip()
            ficha.contacto_emergencia_nombre = request.POST.get('contacto_emergencia_nombre', '').strip()
            ficha.contacto_emergencia_tel   = request.POST.get('contacto_emergencia_tel', '').strip()
            ficha.save()

            registrar_log(request, accion='ver_paciente', paciente=paciente,
                          descripcion='Actualizó ficha médica')
            messages.success(request, 'Ficha médica actualizada correctamente.')

        elif accion == 'agregar_prescripcion':
            medicamento  = request.POST.get('medicamento', '').strip()
            dosis        = request.POST.get('dosis', '').strip()
            fecha_inicio = request.POST.get('fecha_inicio')
            if medicamento and dosis and fecha_inicio:
                fecha_fin = request.POST.get('fecha_fin') or None
                Prescripcion.objects.create(
                    paciente=paciente,
                    medico=request.user,
                    medicamento=medicamento,
                    dosis=dosis,
                    via=request.POST.get('via', 'oral'),
                    frecuencia=request.POST.get('frecuencia'),
                    indicaciones=request.POST.get('indicaciones', '').strip(),
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                )
                messages.success(request, f'Prescripción de {medicamento} agregada.')
            else:
                messages.error(request, 'Medicamento, dosis y fecha de inicio son obligatorios.')

        elif accion == 'desactivar_prescripcion':
            presc_id = request.POST.get('prescripcion_id')
            Prescripcion.objects.filter(pk=presc_id, paciente=paciente).update(activa=False)
            messages.success(request, 'Prescripción marcada como inactiva.')

        elif accion == 'guardar_umbrales':
            tipos = ['glucosa', 'presion_sistolica', 'presion_diastolica', 'saturacion', 'frecuencia']
            for tipo in tipos:
                min_val = request.POST.get(f'min_{tipo}')
                max_val = request.POST.get(f'max_{tipo}')
                if min_val or max_val:
                    UmbralPersonalizado.objects.update_or_create(
                        paciente=paciente,
                        tipo_metrica=tipo,
                        defaults={
                            'valor_min': float(min_val) if min_val else None,
                            'valor_max': float(max_val) if max_val else None,
                        },
                    )
            messages.success(request, 'Umbrales personalizados guardados.')

        return redirect('ficha_medica', paciente_id=paciente_id)

    prescripciones_activas = paciente.prescripciones.filter(activa=True).select_related('medico')
    prescripciones_pasadas = paciente.prescripciones.filter(activa=False).select_related('medico')

    return render(request, 'core/ficha_medica.html', {
        'paciente':               paciente,
        'ficha':                  ficha,
        'prescripciones_activas': prescripciones_activas,
        'prescripciones_pasadas': prescripciones_pasadas,
        'umbrales':               umbrales,
        'tipos_metrica':          UmbralPersonalizado.TIPOS_METRICA,
        'today':                  date.today().isoformat(),
        'vias':                   Prescripcion.VIAS,
        'frecuencias_presc':      Prescripcion.FRECUENCIAS,
    })


@login_required
@medico_required
def agenda(request):
    hoy = date.today()

    if request.method == 'POST':
        paciente_id  = request.POST.get('paciente_id')
        tipo         = request.POST.get('tipo', 'control')
        fecha_hora   = request.POST.get('fecha_hora')
        motivo       = request.POST.get('motivo', '').strip()

        if paciente_id and fecha_hora and motivo:
            paciente = get_object_or_404(Paciente, pk=paciente_id)
            Consulta.objects.create(
                paciente=paciente,
                medico=request.user,
                tipo=tipo,
                fecha_hora=fecha_hora,
                motivo=motivo,
            )
            messages.success(request, f'Cita agendada para {paciente.nombre}.')
        else:
            messages.error(request, 'Paciente, fecha/hora y motivo son obligatorios.')
        return redirect('agenda')

    proximas = (Consulta.objects
                .filter(estado='programada', fecha_hora__date__gte=hoy)
                .select_related('paciente', 'medico')
                .order_by('fecha_hora'))

    hoy_citas = proximas.filter(fecha_hora__date=hoy)
    semana_citas = proximas.filter(fecha_hora__date__gt=hoy)[:20]

    recientes = (Consulta.objects
                 .filter(estado='realizada')
                 .select_related('paciente')
                 .order_by('-fecha_hora')[:10])

    pacientes = Paciente.objects.all().order_by('nombre')

    return render(request, 'core/agenda.html', {
        'hoy':          hoy,
        'hoy_citas':    hoy_citas,
        'semana_citas': semana_citas,
        'recientes':    recientes,
        'pacientes':    pacientes,
        'tipos':        Consulta.TIPOS,
        'today':        hoy.isoformat(),
    })


@login_required
@medico_required
def completar_consulta(request, consulta_id):
    if request.method != 'POST':
        return redirect('agenda')

    consulta = get_object_or_404(Consulta, pk=consulta_id)
    consulta.diagnostico  = request.POST.get('diagnostico', '').strip()
    consulta.indicaciones = request.POST.get('indicaciones', '').strip()
    proxima   = request.POST.get('proxima_cita')
    consulta.proxima_cita = proxima if proxima else None
    consulta.estado       = 'realizada'
    consulta.save()

    registrar_log(request, accion='ver_paciente', paciente=consulta.paciente,
                  descripcion=f'Consulta completada: {consulta.get_tipo_display()}')
    messages.success(request, 'Consulta registrada correctamente.')
    return redirect('agenda')


@login_required
@medico_required
def cambiar_estado_consulta(request, consulta_id):
    if request.method != 'POST':
        return redirect('agenda')

    consulta = get_object_or_404(Consulta, pk=consulta_id)
    nuevo_estado = request.POST.get('estado')
    if nuevo_estado in ('cancelada', 'no_asistio', 'programada'):
        consulta.estado = nuevo_estado
        consulta.save()
    return redirect('agenda')
