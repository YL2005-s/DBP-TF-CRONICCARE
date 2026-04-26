from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

# Infraestructura lista. Para asignar grupo automáticamente al crear un User,
# descomentar y ajustar el bloque receiver de abajo.

# @receiver(post_save, sender=User)
# def asignar_grupo_por_defecto(sender, instance, created, **kwargs):
#     if created:
#         from django.contrib.auth.models import Group
#         grupo, _ = Group.objects.get_or_create(name='Paciente')
#         instance.groups.add(grupo)
