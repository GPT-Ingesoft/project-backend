from services.admin_services import AdminServices
from services.user_services import UserServices

from rest_framework.views    import APIView
from rest_framework.response import Response
from rest_framework          import status


# =============================================================================
# RF_47 — Historial de notificaciones del más reciente al más antiguo
# GET /api/admin/notificaciones/
# =============================================================================

class NotificationHistoryView(APIView):
    authentication_classes = []
    permission_classes     = []

    def get(self, request):
        user_service = UserServices()
        try:
            usuario = user_service.extract_user_from_token(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        if not UserServices.is_lab_technician(usuario):
            return Response({'error': 'Solo el laboratorista puede acceder al historial de notificaciones.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            historial = AdminServices().get_historial_notificaciones()
            return Response({'total': len(historial), 'notificaciones': historial}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Error interno. Contacte al soporte.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# RF_50 — Reporte de fallas: equipos de mayor a menor número de fallas
# GET /api/admin/reportes/fallas/
# =============================================================================

class FailureReportView(APIView):
    authentication_classes = []
    permission_classes     = []

    def get(self, request):
        user_service = UserServices()
        try:
            usuario = user_service.extract_user_from_token(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        if not UserServices.is_lab_technician(usuario):
            return Response({'error': 'Solo el laboratorista puede acceder a este reporte.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            reporte = AdminServices().get_reporte_fallas()
            return Response({'total_equipos': len(reporte), 'equipos': reporte}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Error interno. Contacte al soporte.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# RF_51 — Reporte de tiempos de reparación promedio por equipo
# GET /api/admin/reportes/tiempos-reparacion/
# =============================================================================

class RepairTimeReportView(APIView):
    authentication_classes = []
    permission_classes     = []

    def get(self, request):
        user_service = UserServices()
        try:
            usuario = user_service.extract_user_from_token(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        if not UserServices.is_lab_technician(usuario):
            return Response({'error': 'Solo el laboratorista puede acceder a este reporte.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            reporte = AdminServices().get_reporte_tiempos_reparacion()
            return Response({'total_equipos': len(reporte), 'equipos': reporte}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Error interno. Contacte al soporte.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# RF_52 — Reporte de equipos fuera de servicio con inactividad > umbral
# GET /api/admin/reportes/fuera-de-servicio/?umbral_dias=<número>
#   umbral_dias: días mínimos de inactividad (default: 30)
# =============================================================================

class OutOfServiceReportView(APIView):
    authentication_classes = []
    permission_classes     = []

    def get(self, request):
        user_service = UserServices()
        try:
            usuario = user_service.extract_user_from_token(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        if not UserServices.is_lab_technician(usuario):
            return Response({'error': 'Solo el laboratorista puede acceder a este reporte.'}, status=status.HTTP_403_FORBIDDEN)

        umbral_dias = request.query_params.get('umbral_dias', 30)
        try:
            reporte = AdminServices().get_reporte_equipos_fuera_de_servicio(umbral_dias)
            return Response(reporte, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Error interno. Contacte al soporte.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# RF_53 — Panel principal: listado de equipos activos
# GET /api/panel/equipos-activos/
# Accesible por cualquier usuario autenticado
# =============================================================================

class ActiveEquipmentDashboardView(APIView):
    authentication_classes = []
    permission_classes     = []

    def get(self, request):
        user_service = UserServices()
        try:
            user_service.extract_user_from_token(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            equipos = AdminServices().get_equipos_activos()
            return Response({'total': len(equipos), 'equipos': equipos}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Error interno. Contacte al soporte.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#################### DEBUG ####################

class NotificationHistoryDebugView(APIView):
    authentication_classes = []
    permission_classes     = []

    def get(self, request):
        try:
            historial = AdminServices().get_historial_notificaciones()
            return Response({'total': len(historial), 'notificaciones': historial}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Error interno. Contacte al soporte.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FailureReportDebugView(APIView):
    authentication_classes = []
    permission_classes     = []

    def get(self, request):
        try:
            reporte = AdminServices().get_reporte_fallas()
            return Response({'total_equipos': len(reporte), 'equipos': reporte}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Error interno. Contacte al soporte.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RepairTimeReportDebugView(APIView):
    authentication_classes = []
    permission_classes     = []

    def get(self, request):
        try:
            reporte = AdminServices().get_reporte_tiempos_reparacion()
            return Response({'total_equipos': len(reporte), 'equipos': reporte}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Error interno. Contacte al soporte.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OutOfServiceReportDebugView(APIView):
    authentication_classes = []
    permission_classes     = []

    def get(self, request):
        umbral_dias = request.query_params.get('umbral_dias', 30)
        try:
            reporte = AdminServices().get_reporte_equipos_fuera_de_servicio(umbral_dias)
            return Response(reporte, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Error interno. Contacte al soporte.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ActiveEquipmentDashboardDebugView(APIView):
    authentication_classes = []
    permission_classes     = []

    def get(self, request):
        try:
            equipos = AdminServices().get_equipos_activos()
            return Response({'total': len(equipos), 'equipos': equipos}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Error interno. Contacte al soporte.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
