import re
import secrets
from datetime import timedelta, date
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import transaction
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
    import json
    from collections import Counter
    from django.db.models import Prefetch

    q = request.GET.get('q', '').strip()
    filtro_enfermedad = request.GET.get('enfermedad', '')
    filtro_estado = request.GET.get('estado', '')

    pacientes_qs = Paciente.objects.prefetch_related(
        Prefetch('metricas', queryset=Metrica.objects.order_by('-fecha')),
        Prefetch('alertas', queryset=Alerta.objects.filter(resuelta=False)),
    )
    alertas_criticas = Alerta.objects.filter(resuelta=False, criticidad='critica').count()

    ahora = timezone.now()
    ultimas_24h = ahora - timedelta(hours=24)
    ultimas_48h = ahora - timedelta(hours=48)

    todos = []
    for p in pacientes_qs:
        alertas_p = [a for a in p.alertas.all() if a.criticidad == 'critica' and a.fecha >= ultimas_24h]
        metricas_p = list(p.metricas.all())
        metricas_alerta = [m for m in metricas_p if m.alerta and m.fecha >= ultimas_48h]

        if alertas_p:
            estado = 'critico'
        elif len(metricas_alerta) >= 2:
            estado = 'riesgo'
        else:
            estado = 'estable'

        todos.append({
            'paciente': p,
            'estado': estado,
            'ultima_metrica': metricas_p[0] if metricas_p else None,
        })

    pacientes_seguros = sum(1 for item in todos if item['estado'] == 'estable')
    pacientes_riesgo = sum(1 for item in todos if item['estado'] == 'riesgo')
    pacientes_criticos = sum(1 for item in todos if item['estado'] == 'critico')

    enf_counter = Counter(item['paciente'].get_enfermedad_display() for item in todos)
    enfermedades_chart_json = json.dumps([
        {'label': k, 'count': v}
        for k, v in sorted(enf_counter.items(), key=lambda x: -x[1])
    ])

    filtrados = todos
    if q:
        q_lower = q.lower()
        filtrados = [
            item for item in filtrados
            if q_lower in item['paciente'].nombre.lower() or q in item['paciente'].dni
        ]
    if filtro_enfermedad:
        filtrados = [item for item in filtrados if item['paciente'].enfermedad == filtro_enfermedad]
    if filtro_estado:
        filtrados = [item for item in filtrados if item['estado'] == filtro_estado]

    paginator = Paginator(filtrados, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    params = request.GET.copy()
    params.pop('page', None)
    filtros_qs = params.urlencode()

    return render(request, 'core/dashboard.html', {
        'pacientes': pacientes_qs,
        'pacientes_list': page_obj,
        'page_obj': page_obj,
        'alertas_count': alertas_criticas,
        'pacientes_seguros': pacientes_seguros,
        'pacientes_riesgo': pacientes_riesgo,
        'pacientes_criticos': pacientes_criticos,
        'enfermedades_chart_json': enfermedades_chart_json,
        'q': q,
        'filtro_enfermedad': filtro_enfermedad,
        'filtro_estado': filtro_estado,
        'enfermedades_choices': Paciente.ENFERMEDADES,
        'hay_filtros': bool(q or filtro_enfermedad or filtro_estado),
        'filtros_qs': filtros_qs,
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

        return redirect('detalle_paciente', paciente_id=paciente_id)

    registrar_log(
        request,
        accion='ver_paciente',
        paciente=paciente,
        descripcion=f"Accedió a la ficha de {paciente.nombre}",
    )

    estado_paciente = paciente.calcular_estado()
    metricas = paciente.metricas.all().order_by('-fecha')
    notas = paciente.notas.select_related('medico').all()
    planes = paciente.planes.filter(activo=True)

    ultima_metrica = metricas.first()
    ultima_valor_str = f"{float(ultima_metrica.valor):.1f}" if ultima_metrica else None

    metricas_formateadas = []
    for m in metricas:
        metricas_formateadas.append({
            'metrica': m,
            'valor_str': f"{float(m.valor):.1f}",
            'fecha_str': m.fecha.strftime('%d/%m/%y %H:%M'),
        })

    TIPOS_DISPLAY = [
        ('glucosa', 'Glucosa', 'mg/dL'),
        ('presion', 'Presión Arterial', 'mmHg'),
        ('saturacion', 'Saturación O₂', '%'),
        ('frecuencia', 'Frec. Cardíaca', 'lpm'),
    ]
    ultimas_por_tipo = []
    for tipo, label, unidad in TIPOS_DISPLAY:
        m = paciente.metricas.filter(tipo=tipo).order_by('-fecha').first()
        ultimas_por_tipo.append({
            'tipo': tipo,
            'label': label,
            'unidad': unidad,
            'valor_str': f"{float(m.valor):.1f}" if m else None,
            'alerta': m.alerta if m else False,
            'fecha_str': m.fecha.strftime('%d/%m %H:%M') if m else None,
        })

    periodo = request.GET.get('periodo', '10')
    ahora = timezone.now()

    _tipo_default = {
        'diabetes_t2': 'glucosa', 'diabetes_t1': 'glucosa',
        'hipertension': 'presion', 'asma': 'saturacion',
        'epoc': 'saturacion', 'irc': 'presion',
        'icc': 'frecuencia', 'artritis': 'frecuencia',
    }
    tipo_grafica = request.GET.get('tipo', '') or _tipo_default.get(paciente.enfermedad, 'glucosa')

    TIPOS_DISPLAY_GRAFICA = [
        ('glucosa', 'Glucosa'), ('presion', 'Presión'), ('saturacion', 'Saturación'), ('frecuencia', 'F. Cardíaca'),
    ]
    tipos_disponibles = [
        {'tipo': t, 'label': l, 'count': paciente.metricas.filter(tipo=t).count()}
        for t, l in TIPOS_DISPLAY_GRAFICA
    ]

    if periodo == 'semana':
        desde = ahora - timedelta(days=7)
        metricas_grafica = list(paciente.metricas.filter(tipo=tipo_grafica, fecha__gte=desde).order_by('fecha'))
        periodo_label = 'Últimos 7 días'
    elif periodo == 'mes':
        desde = ahora - timedelta(days=30)
        metricas_grafica = list(paciente.metricas.filter(tipo=tipo_grafica, fecha__gte=desde).order_by('fecha'))
        periodo_label = 'Últimos 30 días'
    else:
        periodo = '10'
        metricas_grafica = list(paciente.metricas.filter(tipo=tipo_grafica).order_by('-fecha')[:10])[::-1]
        periodo_label = 'Últimas 10 mediciones'

    labels = [m.fecha.strftime('%d/%m %H:%M') for m in metricas_grafica]
    valores = [float(m.valor) for m in metricas_grafica]
    alertas = [m.alerta for m in metricas_grafica]

    umbral_min = None
    umbral_max = None
    umbral_custom = paciente.umbrales.filter(tipo_metrica=tipo_grafica).first()
    if umbral_custom:
        umbral_min = umbral_custom.valor_min
        umbral_max = umbral_custom.valor_max
    else:
        _h = Metrica.UMBRALES.get(paciente.enfermedad)
        if _h and _h['tipo'] == tipo_grafica:
            umbral_min = _h['min']
            umbral_max = _h['max']

    tendencia = None
    if len(valores) >= 2 and valores[0] != 0:
        cambio = round((valores[-1] - valores[0]) / valores[0] * 100, 1)
        tendencia = {'pct': abs(cambio), 'sube': cambio > 0, 'neutro': cambio == 0}

    return render(request, 'core/detalle_paciente.html', {
        'paciente': paciente,
        'estado_paciente': estado_paciente,
        'metricas': metricas,
        'metricas_formateadas': metricas_formateadas,
        'ultima_valor_str': ultima_valor_str,
        'ultimas_por_tipo': ultimas_por_tipo,
        'notas': notas,
        'planes': planes,
        'chart_labels':  labels,
        'chart_valores': valores,
        'chart_alertas': alertas,
        'periodo': periodo,
        'periodo_label': periodo_label,
        'total_grafica': len(labels),
        'tipo_grafica': tipo_grafica,
        'tipos_disponibles': tipos_disponibles,
        'umbral_min': umbral_min,
        'umbral_max': umbral_max,
        'tendencia': tendencia,
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

    TIPOS_DISPLAY = [
        ('glucosa', 'Glucosa', 'mg/dL'),
        ('presion', 'Presión Arterial','mmHg'),
        ('saturacion', 'Saturación O2', '%'),
        ('frecuencia', 'Frec. Cardíaca', 'lpm'),
    ]
    ultimas_por_tipo = []
    for tipo, label, unidad in TIPOS_DISPLAY:
        m = paciente.metricas.filter(tipo=tipo).order_by('-fecha').first()
        ultimas_por_tipo.append({
            'tipo': tipo, 'label': label, 'unidad': unidad,
            'valor_str': f"{float(m.valor):.1f}" if m else None,
            'alerta': m.alerta if m else False,
            'fecha_str': m.fecha.strftime('%d/%m %H:%M') if m else None,
        })

    template_path = 'core/reportes/reporte_pdf.html'
    context = {'paciente': paciente, 'metricas': metricas, 'ultimas_por_tipo': ultimas_por_tipo}

    nombre_slug = re.sub(r'[^a-z0-9]+', '_', paciente.nombre.lower().strip()).strip('_')
    filename = f"reporte_croniccare_{nombre_slug}_{paciente.dni}.pdf"
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

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
    pacientes_en_alerta = Paciente.objects.filter(alertas__resuelta=False, alertas__criticidad='critica').distinct().count()
    template_path = 'core/reportes/reporte_general_pdf.html'
    context = {'pacientes': pacientes, 'pacientes_en_alerta': pacientes_en_alerta}

    fecha_str = timezone.localdate().strftime('%Y%m%d')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_croniccare_general_{fecha_str}.pdf"'

    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Error al generar el reporte', status=500)
    return response



@login_required
@medico_required
def bandeja_alertas(request):
    filtro_criticidad = request.GET.get('criticidad', '')
    filtro_enfermedad = request.GET.get('enfermedad', '')

    alertas_raw = Alerta.objects.filter(
        resuelta=False
    ).select_related('paciente', 'metrica').order_by('-fecha')

    if filtro_criticidad:
        alertas_raw = alertas_raw.filter(criticidad=filtro_criticidad)
    if filtro_enfermedad:
        alertas_raw = alertas_raw.filter(paciente__enfermedad=filtro_enfermedad)

    _unidades = {'glucosa': 'mg/dL', 'presion': 'mmHg', 'saturacion': '%', 'frecuencia': 'lpm'}

    alertas_formateadas = []
    for a in alertas_raw:
        valor_str = f"{float(a.metrica.valor):.1f}" if a.metrica else None
        umbral_str = None
        if a.metrica:
            umbral = Metrica.UMBRALES.get(a.paciente.enfermedad)
            if umbral and umbral.get('tipo') == a.metrica.tipo:
                unidad = _unidades.get(a.metrica.tipo, '')
                val = float(a.metrica.valor)
                if umbral.get('max') is not None and val > umbral['max']:
                    umbral_str = f"Umbral máx: {umbral['max']} {unidad}"
                elif umbral.get('min') is not None and val < umbral['min']:
                    umbral_str = f"Umbral mín: {umbral['min']} {unidad}"
        alertas_formateadas.append({
            'alerta': a,
            'valor_str': valor_str,
            'fecha_str': a.fecha.strftime('%d/%m %H:%M'),
            'umbral_str': umbral_str,
        })

    return render(request, 'core/alertas.html', {
        'alertas': alertas_formateadas,
        'filtro_criticidad': filtro_criticidad,
        'filtro_enfermedad': filtro_enfermedad,
        'enfermedades_choices': Paciente.ENFERMEDADES,
        'criticidad_choices': Alerta.CRITICIDAD,
    })


@login_required
@medico_required
def resolver_alerta(request, alerta_id):
    if request.method == 'POST':
        import json as _json
        alerta = get_object_or_404(Alerta, pk=alerta_id)
        alerta.resuelta = True
        alerta.save()

        nota_texto = ''
        if request.headers.get('Content-Type') == 'application/json':
            try:
                nota_texto = _json.loads(request.body).get('nota', '').strip()
            except Exception:
                pass

        if nota_texto:
            NotaClinica.objects.create(
                paciente=alerta.paciente,
                medico=request.user,
                texto=f"[Alerta resuelta] {nota_texto}",
            )

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
    from django.utils import timezone
    from datetime import timedelta

    ahora = timezone.now()
    ultimas_24h = ahora - timedelta(hours=24)
    ultimas_48h = ahora - timedelta(hours=48)

    pacientes = Paciente.objects.prefetch_related(
        'metricas', 'alertas'
    )

    from collections import Counter

    total = 0
    estables = 0
    observacion = 0
    criticos = 0
    criticas = Alerta.objects.filter(resuelta=False, criticidad='critica').count()
    enf_counter = Counter()

    for p in pacientes:
        total += 1
        alertas_p = [a for a in p.alertas.all() if not a.resuelta and a.criticidad == 'critica' and a.fecha >= ultimas_24h]
        metricas_p = list(p.metricas.all())
        metricas_alerta = [m for m in metricas_p if m.alerta and m.fecha >= ultimas_48h]

        if alertas_p:
            criticos += 1
        elif len(metricas_alerta) >= 2:
            observacion += 1
        else:
            estables += 1

        enf_counter[p.get_enfermedad_display()] += 1

    enfermedades = [
        {'label': k, 'count': v}
        for k, v in sorted(enf_counter.items(), key=lambda x: -x[1])
    ]

    return JsonResponse({
        'total': total,
        'estables': estables,
        'observacion': observacion,
        'criticos': criticos,
        'criticas': criticas,
        'enfermedades': enfermedades,
    })


@login_required
@medico_required
def registrar_paciente(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        dni = request.POST.get('dni')
        enfermedad = request.POST.get('enfermedad')

        form_data = {
            'nombre': nombre or '',
            'dni': dni or '',
            'fecha_nacimiento': request.POST.get('fecha_nacimiento', ''),
            'telefono': request.POST.get('telefono', ''),
            'enfermedad': enfermedad or 'diabetes_t2',
        }

        def render_error(msg):
            messages.error(request, msg)
            return render(request, 'core/registro.html', {'form_data': form_data})

        if not nombre or not dni:
            return render_error('Nombre y DNI son obligatorios.')
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$', nombre):
            return render_error('El nombre solo puede contener letras y espacios, sin caracteres especiales.')
        if not dni.isdigit() or len(dni) != 8:
            return render_error('El DNI debe contener exactamente 8 dígitos numéricos.')
        if Paciente.objects.filter(dni=dni).exists():
            return render_error(f"El DNI {dni} ya está registrado en el sistema.")
        if User.objects.filter(username=dni).exists():
            return render_error(f"Ya existe un usuario con el DNI {dni}.")

        password_temp = secrets.token_urlsafe(8)
        fecha_nac = request.POST.get('fecha_nacimiento')
        telefono = request.POST.get('telefono', '').strip()

        with transaction.atomic():
            user = User.objects.create_user(username=dni, password=password_temp)
            grupo_paciente, _ = Group.objects.get_or_create(name='Paciente')
            user.groups.add(grupo_paciente)
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
            user.last_name = request.POST.get('last_name', '').strip()
            user.email = request.POST.get('email', '').strip()
            user.save()

            perfil.especialidad = request.POST.get('especialidad', 'medicina_general')
            perfil.cmp = request.POST.get('cmp', '').strip()
            perfil.telefono = request.POST.get('telefono', '').strip()
            perfil.bio = request.POST.get('bio', '').strip()
            perfil.save()

            registrar_log(
                request,
                accion='ver_paciente',
                descripcion='Actualizó su perfil médico',
            )
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('perfil_medico')

        elif accion == 'cambiar_password':
            password_actual = request.POST.get('password_actual')
            password_nueva = request.POST.get('password_nueva')
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

            ficha.tipo_sangre = request.POST.get('tipo_sangre', '')
            peso = request.POST.get('peso_kg')
            talla = request.POST.get('talla_cm')
            ficha.peso_kg = float(peso) if peso else None
            ficha.talla_cm = float(talla) if talla else None
            ficha.alergias = request.POST.get('alergias', '').strip()
            ficha.cirugias_previas = request.POST.get('cirugias_previas', '').strip()
            ficha.hospitalizaciones = request.POST.get('hospitalizaciones', '').strip()
            ficha.antecedentes_familiares = request.POST.get('antecedentes_familiares', '').strip()
            ficha.historia_enfermedad = request.POST.get('historia_enfermedad', '').strip()
            ficha.contacto_emergencia_nombre = request.POST.get('contacto_emergencia_nombre', '').strip()
            ficha.contacto_emergencia_tel = request.POST.get('contacto_emergencia_tel', '').strip()
            ficha.save()

            registrar_log(request, accion='ver_paciente', paciente=paciente,
                          descripcion='Actualizó ficha médica')
            messages.success(request, 'Ficha médica actualizada correctamente.')

        elif accion == 'agregar_prescripcion':
            medicamento = request.POST.get('medicamento', '').strip()
            dosis = request.POST.get('dosis', '').strip()
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
        'paciente': paciente,
        'ficha': ficha,
        'prescripciones_activas': prescripciones_activas,
        'prescripciones_pasadas': prescripciones_pasadas,
        'umbrales': umbrales,
        'tipos_metrica': UmbralPersonalizado.TIPOS_METRICA,
        'today': date.today().isoformat(),
        'vias': Prescripcion.VIAS,
        'frecuencias_presc': Prescripcion.FRECUENCIAS,
    })


@login_required
@medico_required
def agenda(request):
    hoy = timezone.localdate()

    if request.method == 'POST':
        paciente_id  = request.POST.get('paciente_id')
        tipo = request.POST.get('tipo', 'control')
        fecha_hora = request.POST.get('fecha_hora')
        motivo = request.POST.get('motivo', '').strip()

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

    proximas_qs = proximas.filter(fecha_hora__date__gt=hoy)
    proximas_pag = Paginator(proximas_qs, 10)
    proximas_page = proximas_pag.get_page(request.GET.get('pp', 1))

    recientes_qs = (Consulta.objects
                    .filter(estado='realizada')
                    .select_related('paciente')
                    .order_by('-fecha_hora'))
    recientes_pag = Paginator(recientes_qs, 10)
    recientes_page = recientes_pag.get_page(request.GET.get('rp', 1))

    semana_citas = proximas_page

    pacientes = Paciente.objects.all().order_by('nombre')

    semana_inicio = hoy - timedelta(days=hoy.weekday())
    semana_fin = semana_inicio + timedelta(days=6)
    citas_cal = list(
        Consulta.objects
        .filter(fecha_hora__date__gte=semana_inicio, fecha_hora__date__lte=semana_fin)
        .select_related('paciente')
        .order_by('fecha_hora')
    )
    DIAS_ES = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
    dias_semana = [
        {
            'fecha': semana_inicio + timedelta(days=i),
            'nombre': DIAS_ES[i],
            'citas': [c for c in citas_cal if c.fecha_hora.date() == semana_inicio + timedelta(days=i)],
            'es_hoy': semana_inicio + timedelta(days=i) == hoy,
            'pasado': semana_inicio + timedelta(days=i) < hoy,
        }
        for i in range(7)
    ]

    return render(request, 'core/agenda.html', {
        'hoy': hoy,
        'hoy_citas': hoy_citas,
        'semana_citas': semana_citas,
        'proximas_page': proximas_page,
        'recientes': recientes_page,
        'recientes_page': recientes_page,
        'pacientes': pacientes,
        'tipos': Consulta.TIPOS,
        'today': hoy.isoformat(),
        'dias_semana': dias_semana,
        'semana_inicio': semana_inicio,
        'semana_fin': semana_fin,
    })


@login_required
@medico_required
def completar_consulta(request, consulta_id):
    if request.method != 'POST':
        return redirect('agenda')

    consulta = get_object_or_404(Consulta, pk=consulta_id)
    consulta.diagnostico  = request.POST.get('diagnostico', '').strip()
    consulta.indicaciones = request.POST.get('indicaciones', '').strip()
    proxima = request.POST.get('proxima_cita')
    consulta.proxima_cita = proxima if proxima else None
    consulta.estado = 'realizada'
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
