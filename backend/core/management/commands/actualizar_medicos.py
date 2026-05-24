from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group


class Command(BaseCommand):
    help = 'Actualiza el username de los médicos a su DNI de 8 dígitos'

    def handle(self, *args, **options):
        try:
            grupo = Group.objects.get(name='Medico')
        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                'El grupo "Medico" no existe. Ejecute primero: python manage.py crear_grupos'
            ))
            return

        medicos = grupo.user_set.all().order_by('username')

        if not medicos.exists():
            self.stdout.write(self.style.WARNING('No hay usuarios en el grupo "Medico".'))
            return

        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\n  Médicos registrados ({medicos.count()})\n'
        ))

        actualizados = 0

        for user in medicos:
            self.stdout.write(f'  Usuario actual: {self.style.HTTP_INFO(user.username)}')

            while True:
                nuevo_dni = input('  Nuevo DNI (8 dígitos, Enter para omitir): ').strip()

                if nuevo_dni == '':
                    self.stdout.write(self.style.WARNING('  Omitido.\n'))
                    break

                if not nuevo_dni.isdigit() or len(nuevo_dni) != 8:
                    self.stdout.write(self.style.ERROR(
                        '  Error: el DNI debe contener exactamente 8 dígitos numéricos.'
                    ))
                    continue

                if User.objects.filter(username=nuevo_dni).exclude(pk=user.pk).exists():
                    self.stdout.write(self.style.ERROR(
                        f'  Error: el DNI {nuevo_dni} ya está en uso por otro usuario.'
                    ))
                    continue

                User.objects.filter(pk=user.pk).update(username=nuevo_dni)
                self.stdout.write(self.style.SUCCESS(
                    f'  Actualizado: {user.username} → {nuevo_dni}\n'
                ))
                actualizados += 1
                break

        self.stdout.write(self.style.SUCCESS(
            f'\n  Proceso completado. {actualizados} usuario(s) actualizados.'
        ))
