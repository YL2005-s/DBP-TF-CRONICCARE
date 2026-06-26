import json
from collections import Counter
from datetime import timedelta

from django.contrib.auth.models import User, Group
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone

from .models import (
    Alerta,
    FichaMedica,
    LogAcceso,
    Metrica,
    NotaClinica,
    Paciente,
    PlanCuidado,
)


_TIPO_A_UMBRAL_CUSTOM = {
    'glucosa': 'glucosa',
    'presion': 'presion_sistolica',
    'saturacion': 'saturacion',
    'frecuencia': 'frecuencia',
}


def _umbral_custom(paciente, tipo_metrica_key):
    umbral = paciente.umbrales.filter(tipo_metrica=tipo_metrica_key).first()
    if umbral:
        return umbral.valor_min, umbral.valor_max
    return None, None


def _umbral_estatico(enfermedad, tipo):
    umbral_enfermedad = Metrica.UMBRALES.get(enfermedad)
    if umbral_enfermedad and umbral_enfermedad['tipo'] == tipo:
        return umbral_enfermedad.get('min'), umbral_enfermedad.get('max')
    return None, None


def _umbral_estatico_diastolica(enfermedad):
    umbral_enfermedad = Metrica.UMBRALES.get(enfermedad)
    if umbral_enfermedad and umbral_enfermedad['tipo'] == 'presion':
        return umbral_enfermedad.get('min_diastolica'), umbral_enfermedad.get('max_diastolica')
    return None, None


def _nivel_por_desviacion(porcentaje_desviacion):
    if porcentaje_desviacion > 15:
        return 'critica'
    if porcentaje_desviacion > 5:
        return 'moderada'
    return 'leve'


def _criticidad_valor(valor, umbral_min, umbral_max):
    if umbral_max is not None and valor > umbral_max:
        pct = (valor - umbral_max) / umbral_max * 100
        return _nivel_por_desviacion(pct)
    if umbral_min is not None and valor < umbral_min:
        pct = (umbral_min - valor) / umbral_min * 100
        return _nivel_por_desviacion(pct)
    return None


_ORDEN_CRITICIDAD = {'leve': 1, 'moderada': 2, 'critica': 3}


def _max_criticidad(*niveles):
    validos = [n for n in niveles if n is not None]
    if not validos:
        return None
    return max(validos, key=lambda n: _ORDEN_CRITICIDAD[n])


def calcular_criticidad_metrica(paciente, tipo, valor, valor_diastolica=None):
    custom_key = _TIPO_A_UMBRAL_CUSTOM.get(tipo)
    vmin, vmax = _umbral_custom(paciente, custom_key) if custom_key else (None, None)

    if vmin is None and vmax is None:
        vmin, vmax = _umbral_estatico(paciente.enfermedad, tipo)

    criticidad_principal = _criticidad_valor(valor, vmin, vmax)

    if tipo == 'presion' and valor_diastolica is not None:
        dmin, dmax = _umbral_custom(paciente, 'presion_diastolica')
        if dmin is None and dmax is None:
            dmin, dmax = _umbral_estatico_diastolica(paciente.enfermedad)
        criticidad_diastolica = _criticidad_valor(valor_diastolica, dmin, dmax)
        return _max_criticidad(criticidad_principal, criticidad_diastolica)

    return criticidad_principal


def _valor_display_metrica(metrica):
    if metrica.valor_diastolica is not None:
        return f"{metrica.valor:.0f}/{metrica.valor_diastolica:.0f}"
    return f"{metrica.valor}"


def resincronizar_alertas_paciente(paciente):
    metricas = paciente.metricas.prefetch_related("alertas")

    with transaction.atomic():
        for metrica in metricas:
            criticidad = calcular_criticidad_metrica(
                paciente, metrica.tipo, metrica.valor, metrica.valor_diastolica
            )
            nueva_alerta = criticidad is not None

            if metrica.alerta != nueva_alerta:
                metrica.alerta = nueva_alerta
                metrica.save(update_fields=["alerta"])

            alertas = list(metrica.alertas.all())
            pendientes = [alerta for alerta in alertas if not alerta.resuelta]

            if criticidad is None:
                for alerta in pendientes:
                    alerta.delete()
                continue

            mensaje = f"Valor {criticidad} de {metrica.tipo}: {_valor_display_metrica(metrica)}"
            if pendientes:
                alerta = pendientes[0]
                alerta.criticidad = criticidad
                alerta.mensaje = mensaje
                alerta.save(update_fields=["criticidad", "mensaje"])
            elif not alertas:
                Alerta.objects.create(
                    paciente = paciente,
                    metrica = metrica,
                    mensaje = mensaje,
                    criticidad = criticidad,
                    resuelta = False,
                )


def registrar_log(request, accion, paciente=None, descripcion=""):
    ip = request.META.get("HTTP_X_FORWARDED_FOR")
    if ip:
        ip = ip.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    LogAcceso.objects.create(
        medico=request.user,
        paciente=paciente,
        accion=accion,
        descripcion=descripcion,
        ip=ip,
    )


_TIPO_METRICA_POR_ENFERMEDAD = {
    "diabetes_t2": "glucosa",
    "diabetes_t1": "glucosa",
    "hipertension": "presion",
    "asma": "saturacion",
    "epoc": "saturacion",
    "irc": "presion",
    "icc": "frecuencia",
    "artritis": "frecuencia",
}

TIPOS_METRICA_DISPLAY = [
    ("glucosa", "Glucosa", "mg/dL"),
    ("presion", "Presión Arterial", "mmHg"),
    ("saturacion", "Saturación O₂", "%"),
    ("frecuencia", "Frec. Cardíaca", "lpm"),
]

UNIDADES_METRICA = {t: u for t, _, u in TIPOS_METRICA_DISPLAY}


def tipo_metrica_principal(enfermedad):
    return _TIPO_METRICA_POR_ENFERMEDAD.get(enfermedad, "glucosa")


def clasificar_paciente(alertas_list, metricas_list, ultimas_24h, ultimas_48h):
    alertas_criticas = [
        alerta for alerta in alertas_list
        if alerta.criticidad == "critica" and alerta.fecha >= ultimas_24h
    ]
    metricas_alerta = [
        metrica for metrica in metricas_list
        if metrica.alerta and metrica.fecha >= ultimas_48h
    ]
    if alertas_criticas:
        return "critico"
    if len(metricas_alerta) >= 2:
        return "riesgo"
    return "estable"


def listar_pacientes():
    ahora = timezone.now()
    ultimas_24h = ahora - timedelta(hours=24)
    ultimas_48h = ahora - timedelta(hours=48)

    pacientes_qs = Paciente.objects.prefetch_related(
        Prefetch("metricas", queryset = Metrica.objects.order_by("-fecha")),
        Prefetch("alertas", queryset = Alerta.objects.filter(resuelta=False)),
    )

    resultado = []
    for paciente in pacientes_qs:
        metricas_paciente = list(paciente.metricas.all())
        estado = clasificar_paciente(
            list(paciente.alertas.all()),
            metricas_paciente,
            ultimas_24h,
            ultimas_48h,
        )
        resultado.append({
            "paciente": paciente,
            "estado": estado,
            "ultima_metrica": metricas_paciente[0] if metricas_paciente else None,
        })
    return resultado


def estadisticas_pacientes(items):
    estables = sum(1 for i in items if i["estado"] == "estable")
    riesgo = sum(1 for i in items if i["estado"] == "riesgo")
    criticos = sum(1 for i in items if i["estado"] == "critico")
    alertas_criticas = Alerta.objects.filter(resuelta=False, criticidad="critica").count()

    enfermedades_counter = Counter(i["paciente"].get_enfermedad_display() for i in items)
    enfermedades_chart = json.dumps([
        {"label": k, "count": v}
        for k, v in sorted(enfermedades_counter.items(), key=lambda x: -x[1])
    ])

    return {
        "total_pacientes": len(items),
        "estables": estables,
        "riesgo": riesgo,
        "criticos": criticos,
        "alertas_criticas": alertas_criticas,
        "enfermedades_chart": enfermedades_chart,
    }


def filtrar_pacientes(items, q = "", filtro_enfermedad = "", filtro_estado = ""):
    if q:
        q_lower = q.lower()
        items = [
            i for i in items
            if q_lower in i["paciente"].nombre.lower() or q in i["paciente"].dni
        ]
    if filtro_enfermedad:
        items = [i for i in items if i["paciente"].enfermedad == filtro_enfermedad]
    if filtro_estado:
        items = [i for i in items if i["estado"] == filtro_estado]
    return items


def formatear_valor_metrica(metrica):
    if metrica is None:
        return None
    if metrica.tipo == "presion" and metrica.valor_diastolica is not None:
        return f"{float(metrica.valor):.0f} / {float(metrica.valor_diastolica):.0f}"
    return f"{float(metrica.valor):.1f}"


def ultimas_metricas_por_tipo(paciente):
    resultado = []
    for tipo, label, unidad in TIPOS_METRICA_DISPLAY:
        metrica = paciente.metricas.filter(tipo=tipo).order_by("-fecha").first()
        resultado.append({
            "tipo": tipo,
            "label": label,
            "unidad": unidad,
            "valor_str": formatear_valor_metrica(metrica),
            "alerta": metrica.alerta if metrica else False,
            "fecha_str": metrica.fecha.strftime("%d/%m %H:%M") if metrica else None,
        })
    return resultado


def datos_grafico(paciente, tipo_grafica, periodo):
    ahora = timezone.now()

    if periodo == "semana":
        desde = ahora - timedelta(days=7)
        qs = paciente.metricas.filter(tipo = tipo_grafica, fecha__gte = desde).order_by("fecha")
        periodo_label = "Últimos 7 días"
    elif periodo == "mes":
        desde = ahora - timedelta(days=30)
        qs = paciente.metricas.filter(tipo = tipo_grafica, fecha__gte = desde).order_by("fecha")
        periodo_label = "Últimos 30 días"
    else:
        qs = paciente.metricas.filter(tipo = tipo_grafica).order_by("-fecha")[:10]
        qs = list(reversed(list(qs)))
        periodo_label = "Últimas 10 mediciones"

    metricas = list(qs) if periodo in ("semana", "mes") else qs

    labels = [metrica.fecha.strftime("%d/%m %H:%M") for metrica in metricas]
    valores = [float(metrica.valor) for metrica in metricas]
    alertas = [metrica.alerta for metrica in metricas]

    tendencia = None
    if len(valores) >= 2 and valores[0] != 0:
        cambio = round((valores[-1] - valores[0]) / valores[0] * 100, 1)
        tendencia = {"pct": abs(cambio), "sube": cambio > 0, "neutro": cambio == 0}

    return {
        "labels": labels,
        "valores": valores,
        "alertas": alertas,
        "periodo_label": periodo_label,
        "tendencia": tendencia,
        "total": len(labels),
    }


def umbrales_grafico(paciente, tipo_grafica):
    umbral_custom = paciente.umbrales.filter(tipo_metrica = tipo_grafica).first()
    if umbral_custom:
        return umbral_custom.valor_min, umbral_custom.valor_max

    _h = Metrica.UMBRALES.get(paciente.enfermedad)
    if _h and _h["tipo"] == tipo_grafica:
        return _h["min"], _h["max"]

    return None, None


def obtener_timeline(paciente, metricas, notas):
    eventos = []

    for metrica in metricas[:60]:
        eventos.append({
            "tipo": "metrica",
            "fecha": metrica.fecha,
            "fecha_str": metrica.fecha.strftime("%d %b %Y · %H:%M"),
            "metrica": metrica,
            "valor_str": formatear_valor_metrica(metrica),
            "unidad": UNIDADES_METRICA.get(metrica.tipo, ""),
        })

    for nota in notas[:40]:
        eventos.append({
            "tipo": "nota",
            "fecha": nota.fecha,
            "fecha_str": nota.fecha.strftime("%d %b %Y · %H:%M"),
            "nota": nota,
        })

    alertas_resueltas = (
        paciente.alertas.filter(resuelta=True)
        .select_related("metrica")
        .order_by("-fecha")[:30]
    )
    for alerta in alertas_resueltas:
        eventos.append({
            "tipo": "alerta",
            "fecha": alerta.fecha,
            "fecha_str": alerta.fecha.strftime("%d %b %Y · %H:%M"),
            "alerta": alerta,
            "valor_str": formatear_valor_metrica(alerta.metrica) if alerta.metrica else None,
            "unidad": UNIDADES_METRICA.get(alerta.metrica.tipo, "") if alerta.metrica else "",
        })

    eventos.sort(key=lambda x: x["fecha"], reverse=True)
    return eventos


def crear_paciente(nombre, dni, enfermedad, fecha_nac, telefono):
    import secrets
    password_temp = secrets.token_urlsafe(8)

    with transaction.atomic():
        user = User.objects.create_user(username = dni, password = password_temp)
        grupo_paciente, _ = Group.objects.get_or_create(name = "Paciente")
        user.groups.add(grupo_paciente)
        paciente = Paciente.objects.create(
            user = user,
            nombre = nombre,
            dni = dni,
            enfermedad = enfermedad,
            fecha_nacimiento = fecha_nac if fecha_nac else None,
            telefono = telefono,
        )
        FichaMedica.objects.create(paciente = paciente)

    return paciente, password_temp


def formatear_alertas(alertas_qs):
    resultado = []
    for alerta in alertas_qs:
        umbral_str = None
        if alerta.metrica:
            tipo = alerta.metrica.tipo
            val = float(alerta.metrica.valor)
            unidad = UNIDADES_METRICA.get(tipo, "")

            custom_key = _TIPO_A_UMBRAL_CUSTOM.get(tipo)
            vmin, vmax = _umbral_custom(alerta.paciente, custom_key) if custom_key else (None, None)
            if vmin is None and vmax is None:
                vmin, vmax = _umbral_estatico(alerta.paciente.enfermedad, tipo)

            if vmax is not None and val > vmax:
                umbral_str = f"Umbral máx: {vmax} {unidad}"
            elif vmin is not None and val < vmin:
                umbral_str = f"Umbral mín: {vmin} {unidad}"

        resultado.append({
            "alerta": alerta,
            "valor_str": formatear_valor_metrica(alerta.metrica) if alerta.metrica else None,
            "fecha_str": alerta.fecha.strftime("%d/%m %H:%M"),
            "umbral_str": umbral_str,
        })
    return resultado


