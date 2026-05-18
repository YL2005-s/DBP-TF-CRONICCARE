import re
import secrets
import random
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import Paciente, Metrica, Alerta, NotaClinica


def es_medico(user):
    return user.groups.filter(name='Medico').exists() or user.is_superuser


medico_required = user_passes_test(es_medico, login_url='sin_permiso')


@login_required
@medico_required
def dashboard_medico(request):
    pacientes = Paciente.objects.all()
    alertas_criticas = Alerta.objects.filter(resuelta=False, criticidad='critica').count()

    pacientes_seguros = 0
    for p in pacientes:
        ultima = p.metricas.last()
        if ultima and not ultima.alerta:
            pacientes_seguros += 1

    return render(request, 'core/dashboard.html', {
        'pacientes': pacientes,
        'alertas_count': alertas_criticas,
        'pacientes_seguros': pacientes_seguros,
    })


@login_required
@medico_required
def detalle_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)

    if request.method == 'POST':
        texto = request.POST.get('nota_texto', '').strip()
        if texto:
            NotaClinica.objects.create(
                paciente=paciente,
                medico=request.user,
                texto=texto,
            )
            messages.success(request, 'Nota clínica agregada correctamente.')
        return redirect('detalle_paciente', paciente_id=paciente_id)

    metricas = paciente.metricas.all().order_by('-fecha')
    notas = paciente.notas.select_related('medico').all()

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
        metricas_grafica = paciente.metricas.order_by('fecha')[:10]
        periodo_label = 'Últimas 10 mediciones'

    labels  = [m.fecha.strftime('%d/%m %H:%M') for m in metricas_grafica]
    valores = [float(m.valor) for m in metricas_grafica]
    alertas = [m.alerta for m in metricas_grafica]

    return render(request, 'core/detalle_paciente.html', {
        'paciente': paciente,
        'metricas': metricas,
        'notas': notas,
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

    return redirect('dashboard')


@login_required
@medico_required
def bandeja_alertas(request):
    alertas = Alerta.objects.filter(
        resuelta=False
    ).select_related('paciente', 'metrica').order_by('-fecha')
    return render(request, 'core/alertas.html', {'alertas': alertas})


@login_required
@medico_required
def resolver_alerta(request, alerta_id):
    if request.method == 'POST':
        Alerta.objects.filter(pk=alerta_id).update(resuelta=True)
    return redirect('alertas')


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

        paciente = Paciente.objects.create(
            user=user,
            nombre=nombre,
            dni=dni,
            enfermedad=enfermedad,
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
