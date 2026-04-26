import secrets
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import Paciente, Metrica, Alerta


def es_medico(user):
    return user.groups.filter(name='Medico').exists() or user.is_superuser


medico_required = user_passes_test(es_medico, login_url='sin_permiso')


@login_required
@medico_required
def dashboard_medico(request):
    pacientes = Paciente.objects.all()
    alertas_criticas = Alerta.objects.filter(resuelta=False, criticidad='critica').count()
    return render(request, 'core/dashboard.html', {
        'pacientes': pacientes,
        'alertas_count': alertas_criticas
    })


@login_required
@medico_required
def detalle_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    metricas = paciente.metricas.all().order_by('-fecha')
    return render(request, 'core/detalle_paciente.html', {
        'paciente': paciente,
        'metricas': metricas
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

    return response


@login_required
def simular_metrica(request, paciente_id):
    paciente = Paciente.objects.get(id=paciente_id)
    valor_simulado = 150.0
    es_alerta = valor_simulado > 140

    metrica = Metrica.objects.create(
        paciente=paciente,
        tipo='glucosa',
        valor=valor_simulado,
        alerta=es_alerta
    )

    if es_alerta:
        Alerta.objects.create(
            paciente=paciente,
            metrica=metrica,
            mensaje=f'Glucosa en {valor_simulado:.0f} mg/dL — por encima del umbral (140 mg/dL)',
            criticidad='critica',
        )

    return redirect('dashboard')


@login_required
@medico_required
def bandeja_alertas(request):
    alertas = Metrica.objects.filter(alerta=True).order_by('-fecha')
    return render(request, 'core/alertas.html', {'alertas': alertas})


@login_required
@medico_required
def registrar_paciente(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        dni = request.POST.get('dni')
        enfermedad = request.POST.get('enfermedad')

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
