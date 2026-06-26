import csv
import re
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from ..models import (
    NotaClinica, Paciente, PlanCuidado,
    Prescripcion, FichaMedica, UmbralPersonalizado,
)
from ..permissions import medico_required
from ..services import (
    crear_paciente,
    datos_grafico,
    umbrales_grafico,
    registrar_log,
    TIPOS_METRICA_DISPLAY,
    tipo_metrica_principal,
    ultimas_metricas_por_tipo,
    formatear_valor_metrica,
    obtener_timeline,   
)


@login_required
@medico_required
def detalle_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id = paciente_id)

    if request.method == "POST":
        _manejar_post_detalle(request, paciente, paciente_id)
        return redirect("detalle_paciente", paciente_id = paciente_id)

    registrar_log(
        request,
        accion = "ver_paciente",
        paciente = paciente,
        descripcion = f"Accedió a la ficha de {paciente.nombre}",
    )
    if request.GET.get("tipo") or request.GET.get("periodo"):
        registrar_log(
            request,
            accion = "ver_metricas",
            paciente = paciente,
            descripcion = f"Consultó gráfica de {request.GET.get('tipo', 'métricas')} ({request.GET.get('periodo', '10')})",
        )

    metricas = paciente.metricas.all().order_by("-fecha")
    notas = paciente.notas.select_related("medico").all()
    planes = paciente.planes.filter(activo=True)

    ultima_metrica = metricas.first()
    ultima_metrica_str = formatear_valor_metrica(ultima_metrica)

    metricas_formateadas = [
        {
            "metrica": metrica,
            "valor_str": formatear_valor_metrica(metrica),
            "fecha_str": metrica.fecha.strftime("%d/%m/%y %H:%M"),
        }
        for metrica in metricas
    ]

    periodo = request.GET.get("periodo", "10")
    tipo_grafica = (
        request.GET.get("tipo", "") or tipo_metrica_principal(paciente.enfermedad)
    )

    tipos_disponibles = [
        {"tipo": t, "label": l, "count": paciente.metricas.filter(tipo=t).count()}
        for t, l, _ in TIPOS_METRICA_DISPLAY
    ]

    grafica = datos_grafico(paciente, tipo_grafica, periodo)
    umbral_min, umbral_max = umbrales_grafico(paciente, tipo_grafica)
    timeline = obtener_timeline(paciente, metricas, notas)

    return render(request, "core/detalle_paciente.html", {
        "paciente": paciente,
        "estado_paciente": paciente.calcular_estado(),
        "metricas": metricas,
        "metricas_formateadas": metricas_formateadas,
        "ultima_valor_str": ultima_metrica_str,
        "ultimas_por_tipo": ultimas_metricas_por_tipo(paciente),
        "notas": notas,
        "planes": planes,
        "grafica_etiquetas ":  grafica["labels"],
        "grafica_valores": grafica["valores"],
        "grafica_alertas": grafica["alertas"],
        "periodo": periodo,
        "periodo_label": grafica["periodo_label"],
        "total_mediciones": grafica["total"],
        "tipo_grafica": tipo_grafica,
        "tipos_disponibles": tipos_disponibles,
        "umbral_min": umbral_min,
        "umbral_max": umbral_max,
        "tendencia": grafica["tendencia"],
        "timeline_eventos": timeline,
    })


def _manejar_post_detalle(request, paciente, paciente_id):
    accion = request.POST.get("accion")

    if accion == "agregar_nota":
        texto = request.POST.get("nota_texto", "").strip()
        if texto:
            NotaClinica.objects.create(
                paciente = paciente, 
                medico = request.user, 
                texto = texto
            )
            registrar_log(
                request, accion="agregar_nota", paciente = paciente,
                descripcion=f"Nota: {texto[:50]}...",
            )
            messages.success(request, "Nota clínica agregada correctamente.")

    elif accion == "agregar_plan":
        tipo = request.POST.get("plan_tipo")
        tipo_metrica = request.POST.get("plan_tipo_metrica") or None
        descripcion = request.POST.get("plan_descripcion", "").strip()
        hora = request.POST.get("plan_hora")
        frecuencia = request.POST.get("plan_frecuencia", "diario")

        if descripcion and hora:
            PlanCuidado.objects.create(
                paciente = paciente,
                tipo = tipo,
                tipo_metrica = tipo_metrica if tipo == "metrica" else None,
                descripcion = descripcion,
                hora = hora,
                frecuencia = frecuencia,
                creado_por = request.user,
            )
            registrar_log(
                request, accion="agregar_plan", paciente = paciente,
                descripcion=f"Plan: {descripcion}",
            )
            messages.success(request, "Ítem agregado al plan de cuidados.")

    elif accion == "desactivar_plan":
        plan_id = request.POST.get("plan_id")
        PlanCuidado.objects.filter(pk=plan_id, paciente = paciente).update(activo = False)
        registrar_log(
            request, accion="eliminar_plan", paciente = paciente,
            descripcion=f"Plan eliminado ID: {plan_id}",
        )
        messages.success(request, "Ítem eliminado del plan.")


@login_required
@medico_required
def exportar_csv_metricas(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    metricas = paciente.metricas.all().order_by("-fecha")

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = (
        f'attachment; filename="metricas_{paciente.dni}.csv"'
    )
    response.write("﻿")

    writer = csv.writer(response)
    writer.writerow(["Fecha", "Tipo", "Valor", "Valor Diastólica", "Alerta"])
    for metrica in metricas:
        writer.writerow([
            metrica.fecha.strftime("%d/%m/%Y %H:%M"),
            metrica.get_tipo_display(),
            metrica.valor,
            metrica.valor_diastolica if metrica.valor_diastolica is not None else "",
            "Sí" if metrica.alerta else "No",
        ])

    registrar_log(
        request, accion="generar_pdf", paciente=paciente,
        descripcion=f"Exportó métricas CSV de {paciente.nombre}",
    )
    return response


@login_required
@medico_required
def registrar_paciente(request):
    if request.method != "POST":
        return render(request, "core/registro.html")

    nombre = request.POST.get("nombre")
    dni = request.POST.get("dni")
    enfermedad = request.POST.get("enfermedad")

    form_data = {
        "nombre": nombre or "",
        "dni": dni or "",
        "fecha_nacimiento": request.POST.get("fecha_nacimiento", ""),
        "telefono": request.POST.get("telefono", ""),
        "enfermedad": enfermedad or "diabetes_t2",
    }

    def render_error(msg):
        messages.error(request, msg)
        return render(request, "core/registro.html", {"form_data": form_data})

    if not nombre or not dni:
        return render_error("Nombre y DNI son obligatorios.")
    if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$", nombre):
        return render_error("El nombre solo puede contener letras y espacios, sin caracteres especiales.")
    if not dni.isdigit() or len(dni) != 8:
        return render_error("El DNI debe contener exactamente 8 dígitos numéricos.")
    if Paciente.objects.filter(dni=dni).exists():
        return render_error(f"El DNI {dni} ya está registrado en el sistema.")
    if User.objects.filter(username=dni).exists():
        return render_error(f"Ya existe un usuario con el DNI {dni}.")

    paciente, password_temp = crear_paciente(
        nombre = nombre,
        dni = dni,
        enfermedad = enfermedad,
        fecha_nac = request.POST.get("fecha_nacimiento"),
        telefono = request.POST.get("telefono", "").strip(),
    )
    registrar_log(
        request, accion="registrar_paciente", paciente = paciente,
        descripcion=f"Paciente {nombre} registrado con DNI {dni}",
    )

    return render(request, "core/registro.html", {
        "registro_exitoso": True,
        "credenciales": {"usuario": dni, "password": password_temp},
        "paciente": paciente,
    })


@login_required
@medico_required
def ficha_medica(request, paciente_id):
    paciente = get_object_or_404(Paciente, id = paciente_id)
    ficha, _ = FichaMedica.objects.get_or_create(paciente = paciente)
    umbrales = {u.tipo_metrica: u for u in paciente.umbrales.all()}

    if request.method == "POST":
        _manejar_post_ficha(request, paciente, ficha, paciente_id)
        return redirect("ficha_medica", paciente_id=paciente_id)

    prescripciones_activas = paciente.prescripciones.filter(activa=True).select_related("medico")
    prescripciones_pasadas = paciente.prescripciones.filter(activa=False).select_related("medico")

    return render(request, "core/ficha_medica.html", {
        "paciente": paciente,
        "ficha": ficha,
        "prescripciones_activas": prescripciones_activas,
        "prescripciones_pasadas": prescripciones_pasadas,
        "frecuencias_prescripcion": Prescripcion.FRECUENCIAS,
        "umbrales": umbrales,
        "tipos_metrica": UmbralPersonalizado.TIPOS_METRICA,
        "hoy": date.today().isoformat(),
        "vias": Prescripcion.VIAS,
    })


def _manejar_post_ficha(request, paciente, ficha, paciente_id):
    accion = request.POST.get("accion")

    if accion == "actualizar_ficha":
        fecha_nac = request.POST.get("fecha_nacimiento")
        paciente.fecha_nacimiento = fecha_nac if fecha_nac else None
        paciente.telefono = request.POST.get("telefono", "").strip()
        paciente.save()

        ficha.tipo_sangre = request.POST.get("tipo_sangre", "")
        peso = request.POST.get("peso_kg")
        talla = request.POST.get("talla_cm")
        ficha.peso_kg = float(peso)  if peso  else None
        ficha.talla_cm = float(talla) if talla else None
        ficha.alergias = request.POST.get("alergias", "").strip()
        ficha.cirugias_previas = request.POST.get("cirugias_previas", "").strip()
        ficha.hospitalizaciones = request.POST.get("hospitalizaciones", "").strip()
        ficha.antecedentes_familiares = request.POST.get("antecedentes_familiares", "").strip()
        ficha.historia_enfermedad = request.POST.get("historia_enfermedad", "").strip()
        ficha.contacto_emergencia_nombre = request.POST.get("contacto_emergencia_nombre", "").strip()
        ficha.contacto_emergencia_tel = request.POST.get("contacto_emergencia_tel", "").strip()
        ficha.save()

        registrar_log(request, accion="actualizar_ficha", paciente=paciente,
                      descripcion="Actualizó ficha médica")
        messages.success(request, "Ficha médica actualizada correctamente.")

    elif accion == "agregar_prescripcion":
        medicamento = request.POST.get("medicamento", "").strip()
        dosis = request.POST.get("dosis", "").strip()
        fecha_inicio = request.POST.get("fecha_inicio")
        if medicamento and dosis and fecha_inicio:
            Prescripcion.objects.create(
                paciente = paciente,
                medico = request.user,
                medicamento = medicamento,
                dosis = dosis,
                via = request.POST.get("via", "oral"),
                frecuencia = request.POST.get("frecuencia"),
                indicaciones = request.POST.get("indicaciones", "").strip(),
                fecha_inicio = fecha_inicio,
                fecha_fin = request.POST.get("fecha_fin") or None,
            )
            messages.success(request, f"Prescripción de {medicamento} agregada.")
        else:
            messages.error(request, "Medicamento, dosis y fecha de inicio son obligatorios.")

    elif accion == "desactivar_prescripcion":
        presc_id = request.POST.get("prescripcion_id")
        Prescripcion.objects.filter(pk = presc_id, paciente = paciente).update(activa=False)
        messages.success(request, "Prescripción marcada como inactiva.")

    elif accion == "guardar_umbrales":
        tipos = ["glucosa", "presion_sistolica", "presion_diastolica", "saturacion", "frecuencia"]
        for tipo in tipos:
            min_val = request.POST.get(f"min_{tipo}")
            max_val = request.POST.get(f"max_{tipo}")
            if min_val or max_val:
                UmbralPersonalizado.objects.update_or_create(
                    paciente=paciente,
                    tipo_metrica=tipo,
                    defaults={
                        "valor_min": float(min_val) if min_val else None,
                        "valor_max": float(max_val) if max_val else None,
                    },
                )
        messages.success(request, "Umbrales personalizados guardados.")
