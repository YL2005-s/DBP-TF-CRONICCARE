from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from .models import Paciente, Metrica, Alerta

def dashboard_medico(request):
    pacientes = Paciente.objects.all()
    alertas_criticas = Alerta.objects.filter(resuelta=False, criticidad='Crítica').count()
    return render(request, 'dashboard.html', {
        'pacientes': pacientes,
        'alertas_count': alertas_criticas
    })

def detalle_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    metricas = paciente.metricas.all().order_by('-fecha')
    
    return render(request, 'detalle_paciente.html', {
        'paciente': paciente,
        'metricas': metricas
    })

def exportar_pdf_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    metricas = paciente.metricas.all().order_by('-fecha')
    
    template_path = 'reporte_pdf.html'
    context = {'paciente': paciente, 'metricas': metricas}
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Reporte_{paciente.dni}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)

    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
       return HttpResponse('Error al generar el reporte', status=500)
    return response

def reporte_general_pdf(request):
    pacientes = Paciente.objects.all()
    template_path = 'reporte_general_pdf.html'
    context = {'pacientes': pacientes}
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Reporte_General_CronicCare.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    return response

def simular_metrica(request, paciente_id):
    paciente = Paciente.objects.get(id=paciente_id)
    valor_simulado = 150 
    es_alerta = valor_simulado > 140 
    
    Metrica.objects.create(
        paciente=paciente,
        tipo="Glucosa",
        valor=str(valor_simulado),
        alerta=es_alerta
    )
    return redirect('dashboard')

def bandeja_alertas(request):
    alertas = Metrica.objects.filter(alerta=True).order_by('-fecha')
    return render(request, 'alertas.html', {'alertas': alertas})

def registrar_paciente(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        dni = request.POST.get('dni')
        enfermedad = request.POST.get('enfermedad')

        if Paciente.objects.filter(dni=dni).exists():
            messages.error(request, f"Error: El DNI {dni} ya está registrado en el sistema.")
            return render(request, 'registro.html')

        Paciente.objects.create(nombre=nombre, dni=dni, enfermedad=enfermedad)
        return redirect('dashboard')
        
    return render(request, 'registro.html')