from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = 'Crea los grupos Medico y Paciente con sus permisos base'

    def handle(self, *args, **options):
        medico, created = Group.objects.get_or_create(name='Medico')
        if created:
            self.stdout.write(self.style.SUCCESS("Grupo 'Medico' creado."))
        else:
            self.stdout.write("Grupo 'Medico' ya existía.")

        paciente, created = Group.objects.get_or_create(name='Paciente')
        if created:
            self.stdout.write(self.style.SUCCESS("Grupo 'Paciente' creado."))
        else:
            self.stdout.write("Grupo 'Paciente' ya existía.")

        self.stdout.write(self.style.SUCCESS('Grupos listos.'))
