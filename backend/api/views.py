from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from rest_framework.response import Response
from django.contrib.auth import authenticate
from core.models import Paciente, Metrica, Alerta, NotaClinica, PlanCuidado, Prescripcion, Consulta
from core.services import calcular_criticidad_metrica
from .serializers import PacienteSerializer, MetricaSerializer, AlertaSerializer, NotaClinicaSerializer, PlanCuidadoSerializer, PrescripcionSerializer, ConsultaSerializer


class EsMedico(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.groups.filter(name='Medico').exists()
            or request.user.is_superuser
        )


class PacienteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Paciente.objects.all()
    serializer_class = PacienteSerializer
    permission_classes = [IsAuthenticated, EsMedico]


class MetricaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MetricaSerializer
    permission_classes = [IsAuthenticated, EsMedico]

    def get_queryset(self):
        qs = Metrica.objects.select_related("paciente").order_by("-fecha")
        paciente_id = self.request.query_params.get("paciente")
        if paciente_id:
            qs = qs.filter(paciente_id=paciente_id)
        return qs


class AlertaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AlertaSerializer
    permission_classes = [IsAuthenticated, EsMedico]

    def get_queryset(self):
        qs = Alerta.objects.select_related("paciente", "metrica").order_by("-fecha")
        paciente_id = self.request.query_params.get("paciente")
        resuelta    = self.request.query_params.get("resuelta")
        if paciente_id:
            qs = qs.filter(paciente_id=paciente_id)
        if resuelta is not None:
            qs = qs.filter(resuelta=resuelta.lower() == "true")
        return qs


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
            'fecha_registro': paciente.fecha_registro,
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

    try:
        limit = min(int(request.query_params.get('limit', 20)), 100)
    except (ValueError, TypeError):
        limit = 20

    metricas = Metrica.objects.filter(paciente=paciente).order_by('-fecha')[:limit]
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

    tipo = request.data.get('tipo')
    valor = request.data.get('valor')
    valor_diastolica = request.data.get('valor_diastolica')

    if not tipo or valor is None:
        return Response(
            {'error': 'tipo y valor son requeridos.'},
            status=400
        )

    try:
        valor = float(valor)
    except (ValueError, TypeError):
        return Response({'error': 'El valor debe ser numérico.'}, status=400)

    if valor_diastolica is not None:
        try:
            valor_diastolica = float(valor_diastolica)
        except (ValueError, TypeError):
            return Response({'error': 'valor_diastolica debe ser numérico.'}, status=400)

    criticidad = calcular_criticidad_metrica(paciente, tipo, valor, valor_diastolica)

    metrica = Metrica.objects.create(
        paciente = paciente,
        tipo = tipo,
        valor = valor,
        valor_diastolica = valor_diastolica,
        alerta=criticidad is not None,
    )

    if criticidad:
        valor_display = (
            f"{valor:.0f}/{valor_diastolica:.0f}"
            if valor_diastolica is not None
            else f"{valor}"
        )
        Alerta.objects.create(
            paciente = paciente,
            metrica = metrica,
            mensaje=f"Valor {criticidad} de {tipo}: {valor_display}",
            criticidad=criticidad,
            resuelta=False,
        )

    return Response({
        'id': metrica.id,
        'tipo': metrica.tipo,
        'valor': metrica.valor,
        'valor_diastolica': metrica.valor_diastolica,
        'alerta': metrica.alerta,
        'criticidad': criticidad,
        'fecha': metrica.fecha,
        'mensaje': 'Métrica registrada correctamente.',
    }, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_alertas(request):
    try:
        paciente = request.user.paciente
    except Exception:
        return Response({'error': 'No tienes un perfil de paciente.'}, status=403)

    resuelta = request.query_params.get('resuelta', 'false').lower() == 'true'
    alertas = (
        Alerta.objects
        .filter(paciente=paciente, resuelta=resuelta)
        .select_related('metrica')
        .order_by('-fecha')[:50]
    )
    serializer = AlertaSerializer(alertas, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_prescripciones(request):
    try:
        paciente = request.user.paciente
    except Exception:
        return Response({'error': 'No tienes un perfil de paciente.'}, status=403)

    solo_activas = request.query_params.get('activa', 'true').lower() == 'true'
    prescripciones = (
        Prescripcion.objects
        .filter(paciente=paciente, activa=solo_activas)
        .select_related('medico')
        .order_by('-fecha_inicio')
    )
    serializer = PrescripcionSerializer(prescripciones, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_consultas(request):
    try:
        paciente = request.user.paciente
    except Exception:
        return Response({'error': 'No tienes un perfil de paciente.'}, status=403)

    consultas = (
        Consulta.objects
        .filter(paciente=paciente)
        .select_related('medico')
        .order_by('-fecha_hora')
    )
    serializer = ConsultaSerializer(consultas, many=True)
    return Response(serializer.data)


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

    serializer = PlanCuidadoSerializer(planes, many = True)
    return Response(serializer.data)
