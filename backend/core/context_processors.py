from django.core.cache import cache

from core.models import Alerta

_CACHE_KEY  = "total_alertas_criticas"
_CACHE_SECS = 60


def alertas_pendientes(request):
    if not request.user.is_authenticated:
        return {'total_alertas_pendientes': 0}

    total = cache.get(_CACHE_KEY)
    if total is None:
        total = Alerta.objects.filter(resuelta=False, criticidad='critica').count()
        cache.set(_CACHE_KEY, total, _CACHE_SECS)

    return {'total_alertas_pendientes': total}
