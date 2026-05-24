import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


ENFERMEDAD_MAP = {
    'Diabetes Tipo 2':      'diabetes_t2',
    'Hipertensión Arterial': 'hipertension',
    'Asma':                  'asma',
}

TIPO_MAP = {
    'Glucosa':            'glucosa',
    'Presión Arterial':   'presion',
    'Saturación O2':      'saturacion',
    'Frecuencia Cardíaca':'frecuencia',
}


def normalize_choices(apps, schema_editor):
    Paciente = apps.get_model('core', 'Paciente')
    Metrica  = apps.get_model('core', 'Metrica')

    for p in Paciente.objects.all():
        if p.enfermedad in ENFERMEDAD_MAP:
            p.enfermedad = ENFERMEDAD_MAP[p.enfermedad]
            p.save(update_fields=['enfermedad'])

    for m in Metrica.objects.all():
        if m.tipo in TIPO_MAP:
            m.tipo = TIPO_MAP[m.tipo]
            m.save(update_fields=['tipo'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_remove_metrica_estado_metrica_alerta_and_more'),
    ]

    operations = [
        # 1. Normalizar datos existentes antes de cambios de esquema
        migrations.RunPython(normalize_choices, migrations.RunPython.noop),

        # 2. Paciente.enfermedad → agregar choices
        migrations.AlterField(
            model_name='paciente',
            name='enfermedad',
            field=models.CharField(
                max_length=100,
                choices=[
                    ('diabetes_t2',  'Diabetes Tipo 2'),
                    ('hipertension', 'Hipertensión Arterial'),
                    ('asma',         'Asma'),
                ],
            ),
        ),

        # 3. Metrica.tipo → agregar choices
        migrations.AlterField(
            model_name='metrica',
            name='tipo',
            field=models.CharField(
                max_length=50,
                choices=[
                    ('glucosa',    'Glucosa'),
                    ('presion',    'Presión Arterial'),
                    ('saturacion', 'Saturación O2'),
                    ('frecuencia', 'Frecuencia Cardíaca'),
                ],
            ),
        ),

        # 4. Metrica.valor → CharField → FloatField
        migrations.AlterField(
            model_name='metrica',
            name='valor',
            field=models.FloatField(),
        ),

        # 5. Alerta.criticidad → agregar choices
        migrations.AlterField(
            model_name='alerta',
            name='criticidad',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('critica',  'Crítica'),
                    ('moderada', 'Moderada'),
                    ('leve',     'Leve'),
                ],
            ),
        ),

        # 6. Alerta.fecha → nuevo campo (tabla vacía, default solo para el ALTER TABLE)
        migrations.AddField(
            model_name='alerta',
            name='fecha',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),

        # 7. Alerta.metrica → ForeignKey nullable a Metrica
        migrations.AddField(
            model_name='alerta',
            name='metrica',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='alertas',
                to='core.metrica',
            ),
        ),
    ]
