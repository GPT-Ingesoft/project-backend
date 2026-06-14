from services.request_services import RequestServices
from services.user_services import UserServices

from rest_framework.views    import APIView
from rest_framework.response import Response
from rest_framework          import status


# =============================================================================
# RF_35 — Aprobar solicitud → estado "En proceso" automático
# PATCH /api/solicitudes/<solicitud_id>/aprobar/
# =============================================================================

class RequestApproveView(APIView):
    authentication_classes = []
    permission_classes     = []

    def patch(self, request, solicitud_id):
        service = UserServices()
        try:
            usuario = service.extract_user_from_token(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        if not UserServices.is_lab_technician(usuario):
            return Response({'error': 'Solo el laboratorista puede aprobar solicitudes.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            solicitud = RequestServices().aprobar_solicitud(solicitud_id, usuario)
            return Response({'message': 'Solicitud aprobada. Estado actualizado a En proceso.', 'solicitud': solicitud}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Error interno. Contacte al soporte.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# RF_34 — Consultar horario del laboratorio al revisar una solicitud
# GET /api/solicitudes/horario/?laboratorio=<nombre>
# GET /api/solicitudes/horario/   → devuelve lista de laboratorios
# =============================================================================

class LabScheduleView(APIView):
    authentication_classes = []
    permission_classes     = []

    def get(self, request):
        user_service = UserServices()
        try:
            user_service.extract_user_from_token(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        laboratorio = request.query_params.get('laboratorio', '').strip()
        srv = RequestServices()
        try:
            if not laboratorio:
                laboratorios = srv.get_laboratorios_disponibles()
                return Response({'laboratorios': laboratorios}, status=status.HTTP_200_OK)
            horarios = srv.get_horario_laboratorio(laboratorio)
            return Response({'laboratorio': laboratorio, 'horarios': horarios}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Error interno. Contacte al soporte.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# RF_37 — Cambio manual de estado con motivo obligatorio
# PATCH /api/solicitudes/<solicitud_id>/estado/
# Body JSON: { "estado": "completada", "motivo": "Reparación finalizada." }
# =============================================================================

class RequestStatusView(APIView):
    authentication_classes = []
    permission_classes     = []

    def patch(self, request, solicitud_id):
        user_service = UserServices()
        try:
            usuario = user_service.extract_user_from_token(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        nuevo_estado = request.data.get('estado', '').strip()
        motivo       = request.data.get('motivo', '').strip()

        if not nuevo_estado:
            return Response({'error': "El campo 'estado' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)
        if not motivo:
            return Response({'error': "El campo 'motivo' es obligatorio al cambiar el estado manualmente."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            solicitud = RequestServices().cambiar_estado_manual(solicitud_id, nuevo_estado, motivo, usuario)
            return Response({'message': f"Estado actualizado a '{nuevo_estado}'.", 'solicitud': solicitud}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Error interno. Contacte al soporte.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# RF_38 — Subir archivos adjuntos a una solicitud
# POST /api/solicitudes/<solicitud_id>/adjuntos/
# Body multipart/form-data: archivo (file), tipo, nombre_archivo, descripcion
# =============================================================================

class RequestAttachmentView(APIView):
    authentication_classes = []
    permission_classes     = []

    def post(self, request, solicitud_id):
        user_service = UserServices()
        try:
            usuario = user_service.extract_user_from_token(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        archivo     = request.FILES.get('archivo')
        tipo        = request.data.get('tipo', 'otro')
        nombre      = request.data.get('nombre_archivo', '')
        descripcion = request.data.get('descripcion', '')

        if not archivo:
            return Response({'error': "El campo 'archivo' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)
        if not nombre:
            nombre = archivo.name

        try:
            adjunto = RequestServices().subir_adjunto(
                solicitud_id=solicitud_id, archivo=archivo, tipo=tipo,
                nombre=nombre, tamanio=archivo.size,
                descripcion=descripcion, usuario=usuario,
            )
            return Response({'message': 'Archivo adjunto cargado correctamente.', 'adjunto': adjunto}, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Error interno. Contacte al soporte.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#################### DEBUG ####################

class RequestApproveDebugView(APIView):
    authentication_classes = []
    permission_classes     = []

    def patch(self, request, solicitud_id):
        try:
            solicitud = RequestServices().aprobar_solicitud(solicitud_id, usuario=None)
            return Response({'message': 'Solicitud aprobada.', 'solicitud': solicitud}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Error interno. Contacte al soporte.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RequestStatusDebugView(APIView):
    authentication_classes = []
    permission_classes     = []

    def patch(self, request, solicitud_id):
        nuevo_estado = request.data.get('estado', '').strip()
        motivo       = request.data.get('motivo', '').strip()
        if not nuevo_estado:
            return Response({'error': "El campo 'estado' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)
        if not motivo:
            return Response({'error': "El campo 'motivo' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            solicitud = RequestServices().cambiar_estado_manual(solicitud_id, nuevo_estado, motivo, usuario=None)
            return Response({'message': f"Estado actualizado a '{nuevo_estado}'.", 'solicitud': solicitud}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Error interno. Contacte al soporte.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RequestAttachmentDebugView(APIView):
    authentication_classes = []
    permission_classes     = []

    def post(self, request, solicitud_id):
        archivo     = request.FILES.get('archivo')
        tipo        = request.data.get('tipo', 'otro')
        nombre      = request.data.get('nombre_archivo', '')
        descripcion = request.data.get('descripcion', '')
        if not archivo:
            return Response({'error': "El campo 'archivo' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)
        if not nombre:
            nombre = archivo.name
        try:
            adjunto = RequestServices().subir_adjunto(
                solicitud_id=solicitud_id, archivo=archivo, tipo=tipo,
                nombre=nombre, tamanio=archivo.size,
                descripcion=descripcion, usuario=None,
            )
            return Response({'message': 'Archivo adjunto cargado correctamente.', 'adjunto': adjunto}, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Error interno. Contacte al soporte.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LabScheduleDebugView(APIView):
    authentication_classes = []
    permission_classes     = []

    def get(self, request):
        laboratorio = request.query_params.get('laboratorio', '').strip()
        srv = RequestServices()
        try:
            if not laboratorio:
                return Response({'laboratorios': srv.get_laboratorios_disponibles()}, status=status.HTTP_200_OK)
            horarios = srv.get_horario_laboratorio(laboratorio)
            return Response({'laboratorio': laboratorio, 'horarios': horarios}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Error interno. Contacte al soporte.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
