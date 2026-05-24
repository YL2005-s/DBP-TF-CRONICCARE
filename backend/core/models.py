from django.db import models
from django.contrib.auth.models import User


class Paciente(models.Model):
    ENFERMEDADES = [
        ('diabetes_t2', 'Diabetes Tipo 2'),
        ('hipertension', 'Hipertensión Arterial'),
        ('asma', 'Asma'),
    ]
    user = models.OneToOneField(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='paciente'
    )
    nombre = models.CharField(max_length=100)
    dni = models.CharField(max_length=8, unique=True)
    enfermedad = models.CharField(max_length=100, choices=ENFERMEDADES)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class Metrica(models.Model):
    TIPOS = [
        ('glucosa',    'Glucosa'),
        ('presion',    'Presión Arterial'),
        ('saturacion', 'Saturación O2'),
        ('frecuencia', 'Frecuencia Cardíaca'),
    ]
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='metricas')
    tipo     = models.CharField(max_length=50, choices=TIPOS)
    valor    = models.FloatField()
    alerta   = models.BooleanField(default=False)
    fecha    = models.DateTimeField(auto_now_add=True)


class Alerta(models.Model):
    CRITICIDAD = [
        ('critica',  'Crítica'),
        ('moderada', 'Moderada'),
        ('leve',     'Leve'),
    ]
    paciente   = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    metrica    = models.ForeignKey(Metrica, on_delete=models.SET_NULL, null=True, related_name='alertas')
    mensaje    = models.TextField()
    criticidad = models.CharField(max_length=20, choices=CRITICIDAD)
    resuelta   = models.BooleanField(default=False)
    fecha      = models.DateTimeField(auto_now_add=True)


class NotaClinica(models.Model):
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name='notas'
    )
    medico = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notas'
    )
    texto = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"Nota de {self.medico.get_full_name()} para {self.paciente.nombre}"


class PlanCuidado(models.Model):
    TIPOS = [
        ('medicamento', 'Medicamento'),
        ('metrica',     'Toma de Métrica'),
    ]
    TIPOS_METRICA = [
        ('glucosa',    'Glucosa'),
        ('presion',    'Presión Arterial'),
        ('saturacion', 'Saturación de Oxígeno'),
        ('frecuencia', 'Frecuencia Cardíaca'),
    ]
    FRECUENCIAS = [
        ('diario',   'Diario'),
        ('semanal',  'Semanal'),
        ('mensual',  'Mensual'),
    ]
    paciente     = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name='planes'
    )
    tipo         = models.CharField(max_length=20, choices=TIPOS)
    tipo_metrica = models.CharField(
        max_length=20,
        choices=TIPOS_METRICA,
        blank=True,
        null=True
    )
    descripcion  = models.CharField(max_length=255)
    hora         = models.TimeField()
    frecuencia   = models.CharField(
        max_length=10,
        choices=FRECUENCIAS,
        default='diario'
    )
    activo       = models.BooleanField(default=True)
    fecha_inicio = models.DateField(auto_now_add=True)
    creado_por   = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='planes_creados'
    )

    class Meta:
        ordering = ['hora']

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.descripcion} ({self.hora})"


class LogAcceso(models.Model):
    ACCIONES = [
        ('ver_paciente',       'Ver ficha de paciente'),
        ('ver_metricas',       'Ver métricas'),
        ('agregar_nota',       'Agregar nota clínica'),
        ('agregar_plan',       'Agregar plan de cuidados'),
        ('eliminar_plan',      'Eliminar plan de cuidados'),
        ('marcar_alerta',      'Marcar alerta como resuelta'),
        ('generar_pdf',        'Generar reporte PDF'),
        ('registrar_paciente', 'Registrar paciente'),
        ('simular_metrica',    'Simular métrica'),
    ]
    medico = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='logs'
    )
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs'
    )
    accion      = models.CharField(max_length=30, choices=ACCIONES)
    descripcion = models.TextField(blank=True)
    ip          = models.GenericIPAddressField(null=True, blank=True)
    fecha       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.medico} — {self.get_accion_display()} — {self.fecha}"


class PerfilMedico(models.Model):
    ESPECIALIDADES = [
        ('medicina_general', 'Medicina General'),
        ('cardiologia',      'Cardiología'),
        ('endocrinologia',   'Endocrinología'),
        ('neumologia',       'Neumología'),
        ('medicina_interna', 'Medicina Interna'),
        ('otro',             'Otro'),
    ]
    user         = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil_medico'
    )
    especialidad = models.CharField(
        max_length=30,
        choices=ESPECIALIDADES,
        default='medicina_general'
    )
    cmp      = models.CharField(max_length=20, blank=True, verbose_name='Número CMP')
    telefono = models.CharField(max_length=15, blank=True)
    bio      = models.TextField(blank=True, verbose_name='Descripción profesional')

    def __str__(self):
        return f"Perfil de {self.user.get_full_name()}"
