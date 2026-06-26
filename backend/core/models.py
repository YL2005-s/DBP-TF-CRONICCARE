from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta


class Paciente(models.Model):
    ENFERMEDADES = [
        ('diabetes_t2', 'Diabetes Tipo 2'),
        ('diabetes_t1', 'Diabetes Tipo 1'),
        ('hipertension', 'Hipertensión Arterial'),
        ('asma', 'Asma'),
        ('epoc', 'EPOC'),
        ('irc', 'Insuficiencia Renal Crónica'),
        ('icc', 'Insuficiencia Cardíaca Crónica'),
        ('artritis', 'Artritis Reumatoide'),
        ('otra', 'Otra'),
    ]

    user = models.OneToOneField(User, on_delete = models.SET_NULL, null = True, blank = True, related_name = 'paciente')
    nombre = models.CharField(max_length = 100)
    dni = models.CharField(max_length = 8, unique = True)
    enfermedad = models.CharField(max_length = 100, choices = ENFERMEDADES)
    fecha_nacimiento = models.DateField(null = True, blank = True)
    telefono = models.CharField(max_length = 15, blank = True)
    fecha_registro = models.DateTimeField(auto_now_add = True)

    @property
    def edad(self):
        if not self.fecha_nacimiento:
            return None
        hoy = date.today()
        return hoy.year - self.fecha_nacimiento.year - (
            (hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )

    def calcular_estado(self):
        ahora = timezone.now()
        alerta_critica = self.alertas.filter(
            resuelta=False,
            criticidad='critica',
            fecha__gte=ahora - timedelta(hours=24),
        ).exists()
        if alerta_critica:
            return 'critico'
        metricas_alerta = self.metricas.filter(
            alerta=True,
            fecha__gte=ahora - timedelta(hours=48),
        ).count()
        if metricas_alerta >= 2:
            return 'riesgo'
        return 'estable'

    def __str__(self):
        return self.nombre


class FichaMedica(models.Model):
    TIPOS_SANGRE = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'),  ('O-', 'O-'),
    ]

    paciente = models.OneToOneField(Paciente, on_delete = models.CASCADE, related_name = 'ficha')
    tipo_sangre = models.CharField(max_length = 3, choices = TIPOS_SANGRE, blank = True)
    peso_kg = models.FloatField(null = True, blank = True)
    talla_cm = models.FloatField(null = True, blank = True)
    alergias = models.TextField(blank = True)
    cirugias_previas = models.TextField(blank = True)
    hospitalizaciones = models.TextField(blank = True)
    antecedentes_familiares = models.TextField(blank = True)
    historia_enfermedad = models.TextField(blank = True)
    contacto_emergencia_nombre = models.CharField(max_length = 100, blank = True)
    contacto_emergencia_tel = models.CharField(max_length = 15, blank = True)
    fecha_actualizacion = models.DateTimeField(auto_now = True)

    @property
    def imc(self):
        if self.peso_kg and self.talla_cm:
            talla_m = self.talla_cm / 100
            return round(self.peso_kg / (talla_m ** 2), 1)
        return None

    def __str__(self):
        return f"Ficha de {self.paciente.nombre}"


class Metrica(models.Model):
    TIPOS = [
        ('glucosa', 'Glucosa'),
        ('presion', 'Presión Arterial'),
        ('saturacion', 'Saturación O2'),
        ('frecuencia', 'Frecuencia Cardíaca'),
    ]

    UMBRALES = {
        'diabetes_t2': {'tipo': 'glucosa', 'min': None, 'max': 126},
        'diabetes_t1': {'tipo': 'glucosa', 'min': None, 'max': 126},
        'hipertension': {'tipo': 'presion', 'min': None, 'max': 140, 'max_diastolica': 90},
        'asma': {'tipo': 'saturacion', 'min': 90, 'max': None},
        'epoc': {'tipo': 'saturacion', 'min': 88, 'max': None},
        'irc': {'tipo': 'presion', 'min': None, 'max': 130, 'max_diastolica': 85},
        'icc': {'tipo': 'frecuencia', 'min': 50, 'max': 100},
        'artritis': {'tipo': 'frecuencia', 'min': None, 'max': 100},
    }

    paciente = models.ForeignKey(Paciente, on_delete = models.CASCADE, related_name = 'metricas')
    tipo = models.CharField(max_length=50, choices=TIPOS)
    valor = models.FloatField()
    valor_diastolica = models.FloatField(null = True, blank = True)
    alerta = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)
    

class Alerta(models.Model):
    CRITICIDAD = [
        ('critica', 'Crítica'),
        ('moderada', 'Moderada'),
        ('leve', 'Leve'),
    ]

    paciente = models.ForeignKey(Paciente, on_delete = models.CASCADE, related_name = 'alertas')
    metrica = models.ForeignKey(Metrica, on_delete = models.SET_NULL, null = True, related_name = 'alertas')
    mensaje = models.TextField()
    criticidad = models.CharField(max_length = 20, choices = CRITICIDAD)
    resuelta = models.BooleanField(default = False)
    fecha = models.DateTimeField(auto_now_add = True)


class UmbralPersonalizado(models.Model):
    TIPOS_METRICA = [
        ('glucosa', 'Glucosa (mg/dL)'),
        ('presion_sistolica', 'Presión Sistólica (mmHg)'),
        ('presion_diastolica', 'Presión Diastólica (mmHg)'),
        ('saturacion', 'Saturación O2 (%)'),
        ('frecuencia', 'Frecuencia Cardíaca (lpm)'),
    ]
    paciente = models.ForeignKey(Paciente, on_delete = models.CASCADE, related_name = 'umbrales')
    tipo_metrica = models.CharField(max_length = 30, choices = TIPOS_METRICA)
    valor_min = models.FloatField(null = True, blank = True)
    valor_max = models.FloatField(null = True, blank = True)

    class Meta:
        unique_together = ('paciente', 'tipo_metrica')

    def __str__(self):
        return f"Umbral {self.get_tipo_metrica_display()} — {self.paciente.nombre}"


class Consulta(models.Model):
    TIPOS = [
        ('primera_vez', 'Primera vez'),
        ('control', 'Control rutinario'),
        ('seguimiento', 'Seguimiento'),
        ('urgencia', 'Urgencia'),
    ]
    ESTADOS = [
        ('programada', 'Programada'),
        ('realizada', 'Realizada'),
        ('cancelada', 'Cancelada'),
        ('no_asistio', 'No asistió'),
    ]
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='consultas')
    medico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='consultas')
    tipo = models.CharField(max_length=20, choices=TIPOS, default='control')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='programada')
    fecha_hora = models.DateTimeField()
    motivo = models.CharField(max_length=300)
    diagnostico = models.TextField(blank=True)
    indicaciones = models.TextField(blank=True)
    proxima_cita = models.DateField(null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha_hora']

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.paciente.nombre} ({self.fecha_hora:%d/%m/%Y})"


class NotaClinica(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete = models.CASCADE, related_name = 'notas')
    medico = models.ForeignKey(User, on_delete = models.CASCADE, related_name = 'notas')
    texto = models.TextField()
    fecha = models.DateTimeField(auto_now_add = True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"Nota de {self.medico.get_full_name()} para {self.paciente.nombre}"


class PlanCuidado(models.Model):
    TIPOS = [
        ('medicamento', 'Medicamento'),
        ('metrica', 'Toma de Métrica'),
    ]
    TIPOS_METRICA = [
        ('glucosa', 'Glucosa'),
        ('presion', 'Presión Arterial'),
        ('saturacion', 'Saturación de Oxígeno'),
        ('frecuencia', 'Frecuencia Cardíaca'),
    ]
    FRECUENCIAS = [
        ('diario', 'Diario'),
        ('semanal', 'Semanal'),
        ('mensual', 'Mensual'),
    ]
    
    paciente = models.ForeignKey(Paciente, on_delete = models.CASCADE, related_name = 'planes')
    tipo = models.CharField(max_length = 20, choices = TIPOS)
    tipo_metrica = models.CharField(max_length = 20, choices = TIPOS_METRICA, blank = True, null = True)
    descripcion = models.CharField(max_length = 255)
    hora = models.TimeField()
    frecuencia = models.CharField(max_length = 10, choices = FRECUENCIAS, default = 'diario')
    activo = models.BooleanField(default = True)
    fecha_inicio = models.DateField(auto_now_add = True)
    creado_por = models.ForeignKey(User, on_delete = models.SET_NULL, null = True, related_name = 'planes_creados')

    class Meta:
        ordering = ['hora']

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.descripcion} ({self.hora})"


class Prescripcion(models.Model):
    VIAS = [
        ('oral', 'Oral'),
        ('iv', 'Intravenosa'),
        ('sc', 'Subcutánea'),
        ('im', 'Intramuscular'),
        ('topica', 'Tópica'),
        ('inhalada', 'Inhalada'),
    ]
    FRECUENCIAS = [
        ('cada_4h', 'Cada 4 horas'),
        ('cada_6h', 'Cada 6 horas'),
        ('cada_8h', 'Cada 8 horas'),
        ('cada_12h', 'Cada 12 horas'),
        ('cada_24h', 'Una vez al día'),
        ('segun_necesidad', 'Según necesidad'),
    ]
    paciente = models.ForeignKey(Paciente, on_delete = models.CASCADE, related_name = 'prescripciones')
    medico = models.ForeignKey(User, on_delete = models.SET_NULL, null = True, related_name = 'prescripciones')
    medicamento = models.CharField(max_length = 200)
    dosis = models.CharField(max_length = 100)
    via = models.CharField(max_length = 20, choices = VIAS, default = 'oral')
    frecuencia = models.CharField(max_length = 20, choices = FRECUENCIAS)
    indicaciones = models.TextField(blank = True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null = True, blank = True)
    activa = models.BooleanField(default = True)
    fecha_registro = models.DateTimeField(auto_now_add = True)

    class Meta:
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"{self.medicamento} {self.dosis} — {self.paciente.nombre}"


class PerfilMedico(models.Model):
    ESPECIALIDADES = [
        ('medicina_general', 'Medicina General'),
        ('cardiologia', 'Cardiología'),
        ('endocrinologia', 'Endocrinología'),
        ('neumologia', 'Neumología'),
        ('medicina_interna', 'Medicina Interna'),
        ('otro', 'Otro'),
    ]
    user = models.OneToOneField(User, on_delete = models.CASCADE, related_name = 'perfil_medico')
    especialidad = models.CharField(max_length = 30, choices = ESPECIALIDADES, default = 'medicina_general')
    cmp = models.CharField(max_length = 20, blank = True, verbose_name = 'Número CMP')
    telefono = models.CharField(max_length = 15, blank = True)
    bio = models.TextField(blank = True, verbose_name = 'Descripción profesional')

    def __str__(self):
        return f"Perfil de {self.user.get_full_name()}"


class LogAcceso(models.Model):
    ACCIONES = [
        ('ver_paciente', 'Ver ficha de paciente'),
        ('ver_metricas', 'Ver métricas'),
        ('agregar_nota', 'Agregar nota clínica'),
        ('agregar_plan', 'Agregar plan de cuidados'),
        ('eliminar_plan', 'Eliminar plan de cuidados'),
        ('marcar_alerta', 'Marcar alerta como resuelta'),
        ('generar_pdf', 'Generar reporte PDF'),
        ('exportar_csv', 'Exportar métricas CSV'),
        ('registrar_paciente', 'Registrar paciente'),
        ('completar_consulta', 'Completar consulta'),
        ('actualizar_ficha', 'Actualizar ficha médica'),
        ('actualizar_perfil', 'Actualizar perfil médico'),
    ]
    
    medico = models.ForeignKey(User, on_delete = models.SET_NULL, null = True, related_name = 'logs')
    paciente = models.ForeignKey(Paciente, on_delete = models.SET_NULL, null = True, blank = True, related_name = 'logs')
    accion = models.CharField(max_length = 30, choices = ACCIONES)
    descripcion = models.TextField(blank = True)
    ip = models.GenericIPAddressField(null = True, blank = True)
    fecha = models.DateTimeField(auto_now_add = True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.medico} — {self.get_accion_display()} — {self.fecha}"
