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
    """Devuelve (min, max) desde UmbralPersonalizado o (None, None)."""
    u = paciente.umbrales.filter(tipo_metrica=tipo_metrica_key).first()
    if u:
        return u.valor_min, u.valor_max
    return None, None


def _umbral_estatico(enfermedad, tipo):
    """Devuelve (min, max) desde Metrica.UMBRALES o (None, None)."""
    h = Metrica.UMBRALES.get(enfermedad)
    if h and h['tipo'] == tipo:
        return h.get('min'), h.get('max')
    return None, None


def _umbral_estatico_diastolica(enfermedad):
    """Devuelve (min, max) diastólica desde UMBRALES o (None, None)."""
    h = Metrica.UMBRALES.get(enfermedad)
    if h and h['tipo'] == 'presion':
        return h.get('min_diastolica'), h.get('max_diastolica')
    return None, None


def _nivel_por_desviacion(pct):
    """Traduce % de desviación del umbral a nivel de criticidad."""
    if pct > 15:
        return 'critica'
    if pct > 5:
        return 'moderada'
    return 'leve'


def _criticidad_valor(valor, umbral_min, umbral_max):
    """Compara un valor contra sus umbrales y devuelve la criticidad o None."""
    if umbral_max is not None and valor > umbral_max:
        pct = (valor - umbral_max) / umbral_max * 100
        return _nivel_por_desviacion(pct)
    if umbral_min is not None and valor < umbral_min:
        pct = (umbral_min - valor) / umbral_min * 100
        return _nivel_por_desviacion(pct)
    return None


_ORDEN_CRITICIDAD = {'leve': 1, 'moderada': 2, 'critica': 3}


def _max_criticidad(*niveles):
    """Devuelve el nivel más grave entre varios (o None si todos son None)."""
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


def clasificar_paciente(paciente, alertas_list, metricas_list, ultimas_24h, ultimas_48h):
    """Devuelve el estado ('critico', 'riesgo', 'estable') de un paciente."""
    alertas_criticas = [
        a for a in alertas_list
        if a.criticidad == "critica" and a.fecha >= ultimas_24h
    ]
    metricas_alerta = [
        m for m in metricas_list
        if m.alerta and m.fecha >= ultimas_48h
    ]
    if alertas_criticas:
        return "critico"
    if len(metricas_alerta) >= 2:
        return "riesgo"
    return "estable"


def construir_lista_pacientes():
    """
    Retorna una lista de dicts con {paciente, estado, ultima_metrica}
    para todos los pacientes, ordenada para el dashboard.
    """
    ahora = timezone.now()
    ultimas_24h = ahora - timedelta(hours=24)
    ultimas_48h = ahora - timedelta(hours=48)

    pacientes_qs = Paciente.objects.prefetch_related(
        Prefetch("metricas", queryset=Metrica.objects.order_by("-fecha")),
        Prefetch("alertas", queryset=Alerta.objects.filter(resuelta=False)),
    )

    resultado = []
    for p in pacientes_qs:
        metricas_p = list(p.metricas.all())
        estado = clasificar_paciente(
            p,
            list(p.alertas.all()),
            metricas_p,
            ultimas_24h,
            ultimas_48h,
        )
        resultado.append({
            "paciente": p,
            "estado": estado,
            "ultima_metrica": metricas_p[0] if metricas_p else None,
        })
    return resultado


def estadisticas_dashboard(items):
    """Calcula conteos y datos del gráfico a partir de la lista de items."""
    estables = sum(1 for i in items if i["estado"] == "estable")
    riesgo  = sum(1 for i in items if i["estado"] == "riesgo")
    criticos = sum(1 for i in items if i["estado"] == "critico")
    alertas_criticas = Alerta.objects.filter(resuelta=False, criticidad="critica").count()

    enf_counter = Counter(i["paciente"].get_enfermedad_display() for i in items)
    enfermedades_chart = json.dumps([
        {"label": k, "count": v}
        for k, v in sorted(enf_counter.items(), key=lambda x: -x[1])
    ])

    return {
        "pacientes_seguros": estables,
        "pacientes_riesgo": riesgo,
        "pacientes_criticos": criticos,
        "alertas_count": alertas_criticas,
        "enfermedades_chart_json": enfermedades_chart,
    }


def filtrar_items_dashboard(items, q="", filtro_enfermedad="", filtro_estado=""):
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


def _valor_str(m):
    """Formatea el valor de una métrica. Presión: '120/80', resto: '98.6'."""
    if m is None:
        return None
    if m.tipo == "presion" and m.valor_diastolica is not None:
        return f"{float(m.valor):.0f}/{float(m.valor_diastolica):.0f}"
    return f"{float(m.valor):.1f}"


def ultimas_metricas_por_tipo(paciente):
    resultado = []
    for tipo, label, unidad in TIPOS_METRICA_DISPLAY:
        m = paciente.metricas.filter(tipo=tipo).order_by("-fecha").first()
        resultado.append({
            "tipo": tipo,
            "label": label,
            "unidad": unidad,
            "valor_str": _valor_str(m),
            "alerta": m.alerta if m else False,
            "fecha_str": m.fecha.strftime("%d/%m %H:%M") if m else None,
        })
    return resultado


def datos_grafica(paciente, tipo_grafica, periodo):
    ahora = timezone.now()

    if periodo == "semana":
        desde = ahora - timedelta(days=7)
        qs = paciente.metricas.filter(tipo=tipo_grafica, fecha__gte=desde).order_by("fecha")
        periodo_label = "Últimos 7 días"
    elif periodo == "mes":
        desde = ahora - timedelta(days=30)
        qs = paciente.metricas.filter(tipo=tipo_grafica, fecha__gte=desde).order_by("fecha")
        periodo_label = "Últimos 30 días"
    else:
        qs = paciente.metricas.filter(tipo=tipo_grafica).order_by("-fecha")[:10]
        qs = list(reversed(list(qs)))
        periodo_label = "Últimas 10 mediciones"

    metricas = list(qs) if periodo in ("semana", "mes") else qs

    labels  = [m.fecha.strftime("%d/%m %H:%M") for m in metricas]
    valores = [float(m.valor) for m in metricas]
    alertas = [m.alerta for m in metricas]

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


def umbrales_para_grafica(paciente, tipo_grafica):
    umbral_custom = paciente.umbrales.filter(tipo_metrica=tipo_grafica).first()
    if umbral_custom:
        return umbral_custom.valor_min, umbral_custom.valor_max

    _h = Metrica.UMBRALES.get(paciente.enfermedad)
    if _h and _h["tipo"] == tipo_grafica:
        return _h["min"], _h["max"]

    return None, None


def construir_timeline(paciente, metricas, notas):
    eventos = []

    for m in metricas[:60]:
        eventos.append({
            "tipo": "metrica",
            "fecha": m.fecha,
            "fecha_str": m.fecha.strftime("%d %b %Y · %H:%M"),
            "metrica": m,
            "valor_str": _valor_str(m),
            "unidad": UNIDADES_METRICA.get(m.tipo, ""),
        })

    for n in notas[:40]:
        eventos.append({
            "tipo": "nota",
            "fecha": n.fecha,
            "fecha_str": n.fecha.strftime("%d %b %Y · %H:%M"),
            "nota": n,
        })

    alertas_resueltas = (
        paciente.alertas.filter(resuelta=True)
        .select_related("metrica")
        .order_by("-fecha")[:30]
    )
    for a in alertas_resueltas:
        eventos.append({
            "tipo": "alerta",
            "fecha": a.fecha,
            "fecha_str": a.fecha.strftime("%d %b %Y · %H:%M"),
            "alerta": a,
            "valor_str": _valor_str(a.metrica) if a.metrica else None,
            "unidad": UNIDADES_METRICA.get(a.metrica.tipo, "") if a.metrica else "",
        })

    eventos.sort(key=lambda x: x["fecha"], reverse=True)
    return eventos


def crear_paciente(nombre, dni, enfermedad, fecha_nac, telefono):
    """Crea User + Paciente + FichaMedica en una transacción atómica."""
    import secrets
    password_temp = secrets.token_urlsafe(8)

    with transaction.atomic():
        user = User.objects.create_user(username=dni, password=password_temp)
        grupo_paciente, _ = Group.objects.get_or_create(name="Paciente")
        user.groups.add(grupo_paciente)
        paciente = Paciente.objects.create(
            user = user,
            nombre = nombre,
            dni = dni,
            enfermedad = enfermedad,
            fecha_nacimiento = fecha_nac if fecha_nac else None,
            telefono = telefono,
        )
        FichaMedica.objects.create(paciente=paciente)

    return paciente, password_temp


def formatear_alertas(alertas_qs):
    resultado = []
    for a in alertas_qs:
        umbral_str = None
        if a.metrica:
            tipo   = a.metrica.tipo
            val    = float(a.metrica.valor)
            unidad = UNIDADES_METRICA.get(tipo, "")

            custom_key = _TIPO_A_UMBRAL_CUSTOM.get(tipo)
            vmin, vmax = _umbral_custom(a.paciente, custom_key) if custom_key else (None, None)
            if vmin is None and vmax is None:
                vmin, vmax = _umbral_estatico(a.paciente.enfermedad, tipo)

            if vmax is not None and val > vmax:
                umbral_str = f"Umbral máx: {vmax} {unidad}"
            elif vmin is not None and val < vmin:
                umbral_str = f"Umbral mín: {vmin} {unidad}"

        resultado.append({
            "alerta": a,
            "valor_str": _valor_str(a.metrica) if a.metrica else None,
            "fecha_str": a.fecha.strftime("%d/%m %H:%M"),
            "umbral_str": umbral_str,
        })
    return resultado


