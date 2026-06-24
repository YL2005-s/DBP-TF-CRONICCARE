from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from rest_framework.response import Response
from django.contrib.auth import authenticate
from core.models import Paciente, Metrica, Alerta, NotaClinica, PlanCuidado
from .serializers import PacienteSerializer, MetricaSerializer, AlertaSerializer, NotaClinicaSerializer, PlanCuidadoSerializer


class EsMedico(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.groups.filter(name='Medico').exists()
            or request.user.is_superuser
        )


class PacienteViewSet(viewsets.ModelViewSet):
    queryset = Paciente.objects.all()
    serializer_class = PacienteSerializer
    permission_classes = [IsAuthenticated, EsMedico]


class MetricaViewSet(viewsets.ModelViewSet):
    queryset = Metrica.objects.all()
    serializer_class = MetricaSerializer
    permission_classes = [IsAuthenticated, EsMedico]


class AlertaViewSet(viewsets.ModelViewSet):
    queryset = Alerta.objects.all()
    serializer_class = AlertaSerializer
    permission_classes = [IsAuthenticated, EsMedico]


class NotaClinicaViewSet(viewsets.ModelViewSet):
    queryset = NotaClinica.objects.all()
    serializer_class = NotaClinicaSerializer
    permission_classes = [IsAuthenticated, EsMedico]

    def perform_create(self, serializer):
        serializer.save(medico=self.request.user)


class PlanCuidadoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class   = PlanCuidadoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Medico').exists():
            return PlanCuidado.objects.filter(activo=True)
        try:
            paciente = user.paciente
            return PlanCuidado.objects.filter(
                paciente=paciente,
                activo=True
            )
        except Exception:
            return PlanCuidado.objects.none()


@api_view(['POST'])
@permission_classes([AllowAny])
def login_token(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {'error': 'DNI y contraseña son requeridos.'},
            status=400
        )

    user = authenticate(username=username, password=password)

    if not user:
        return Response(
            {'error': 'DNI o contraseña incorrectos.'},
            status=401
        )

    if not user.is_active:
        return Response(
            {'error': 'Usuario inactivo.'},
            status=403
        )

    token, _ = Token.objects.get_or_create(user=user)

    paciente_data = None
    try:
        paciente = user.paciente
        paciente_data = {
            'id': paciente.id,
            'nombre': paciente.nombre,
            'dni': paciente.dni,
            'enfermedad': paciente.enfermedad,
            'enfermedad_display': paciente.get_enfermedad_display(),
        }
    except Exception:
        paciente_data = None

    return Response({
        'token': token.key,
        'user_id': user.id,
        'username': user.username,
        'nombre': user.get_full_name() or user.username,
        'rol': 'medico' if user.groups.filter(name='Medico').exists() else 'paciente',
        'paciente': paciente_data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_metricas(request):
    try:
        paciente = request.user.paciente
    except Exception:
        return Response(
            {'error': 'No tienes un perfil de paciente.'},
            status=403
        )

    metricas = Metrica.objects.filter(
        paciente=paciente
    ).order_by('-fecha')[:20]

    serializer = MetricaSerializer(metricas, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def registrar_metrica_movil(request):
    try:
        paciente = request.user.paciente
    except Exception:
        return Response(
            {'error': 'No tienes un perfil de paciente.'},
            status=403
        )

    tipo  = request.data.get('tipo')
    valor = request.data.get('valor')

    if not tipo or valor is None:
        return Response(
            {'error': 'tipo y valor son requeridos.'},
            status=400
        )

    try:
        valor = float(valor)
    except (ValueError, TypeError):
        return Response(
            {'error': 'El valor debe ser numérico.'},
            status=400
        )

    es_alerta = Metrica.calcular_alerta(paciente.enfermedad, valor)

    metrica = Metrica.objects.create(
        paciente=paciente,
        tipo=tipo,
        valor=valor,
        alerta=es_alerta,
    )

    if es_alerta:
        Alerta.objects.create(
            paciente=paciente,
            metrica=metrica,
            mensaje=f"Valor crítico de {tipo}: {valor}",
            criticidad='critica',
            resuelta=False,
        )

    return Response({
        'id': metrica.id,
        'tipo': metrica.tipo,
        'valor': metrica.valor,
        'alerta': metrica.alerta,
        'fecha': metrica.fecha,
        'mensaje': 'Métrica registrada correctamente.',
    }, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mi_plan_cuidados(request):
    try:
        paciente = request.user.paciente
    except Exception:
        return Response(
            {'error': 'No tienes un perfil de paciente.'},
            status=403
        )

    planes = PlanCuidado.objects.filter(
        paciente=paciente,
        activo=True,
    ).order_by('hora')

    serializer = PlanCuidadoSerializer(planes, many=True)
    return Response(serializer.data)
