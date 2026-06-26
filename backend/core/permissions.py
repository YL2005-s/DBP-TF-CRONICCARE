from django.contrib.auth.decorators import user_passes_test


def es_medico(user):
    return user.groups.filter(name="Medico").exists() or user.is_superuser


medico_required = user_passes_test(es_medico, login_url="sin_permiso")
