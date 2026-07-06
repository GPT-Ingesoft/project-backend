from rest_framework.response import Response
from rest_framework import status
from information_app.services.admin_services import AdminServices, UMBRAL_DIAS_DEFAULT
from information_app.controllers.controller_utils import handle_exceptions, BaseAPIView, validate_json_request

class NotificationHistoryView(BaseAPIView):
    @handle_exceptions
    def get(self, request):
        self.get_lab_technician(request)
        historial = AdminServices().get_notification_history()
        return Response(
            {'total': len(historial),'notificaciones': historial},
            status=status.HTTP_200_OK
        )

class NotificationDetailView(BaseAPIView):
    @handle_exceptions
    def get(self, request, notification_id):
        self.get_lab_technician(request)
        notification = AdminServices().get_notification(notification_id)
        return Response(
            {'notificacion': notification},
            status=status.HTTP_200_OK,
        )

class RequestDashboardView(BaseAPIView):
    @handle_exceptions
    def get(self, request):
        self.get_lab_technician(request)
        return Response(
            AdminServices().get_request_dashboard(),
            status=status.HTTP_200_OK,
        )

class FailureReportView(BaseAPIView):
    @handle_exceptions
    def get(self, request):
        self.get_lab_technician_or_technician(request)
        reporte = AdminServices().get_failure_report()
        return Response(
            {'total_equipos': len(reporte), 'equipos': reporte},
            status=status.HTTP_200_OK
        )

class RepairTimeReportView(BaseAPIView):
    @handle_exceptions
    def get(self, request):
        self.get_lab_technician_or_technician(request)
        reporte = AdminServices().get_repair_time_report()
        return Response(
            {'total_equipos': len(reporte), 'equipos': reporte},
            status=status.HTTP_200_OK
        )

class OutOfServiceReportView(BaseAPIView):
    @handle_exceptions
    def get(self, request):
        self.get_lab_technician_or_technician(request)
        umbral_dias = request.query_params.get('umbral_dias', None)
        return Response(
            AdminServices().get_out_of_service_equipment_report(umbral_dias),
            status=status.HTTP_200_OK,
        )

class OutOfServiceThresholdView(BaseAPIView):
    @handle_exceptions
    def get(self, request):
        self.get_lab_technician_or_technician(request)
        return Response(
            AdminServices().get_out_of_service_threshold(),
            status=status.HTTP_200_OK,
        )

    @handle_exceptions
    def patch(self, request):
        self.get_lab_technician(request)
        data = validate_json_request(request)
        umbral_dias = data.get('umbral_dias')
        if umbral_dias is None:
            return Response(
                {'error': "El campo 'umbral_dias' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        result = AdminServices().set_out_of_service_threshold(umbral_dias)
        return Response(result, status=status.HTTP_200_OK)

class ActiveEquipmentDashboardView(BaseAPIView):
    @handle_exceptions
    def get(self, request):
        self.get_user(request)
        equipos = AdminServices().get_active_equipment()
        return Response(
            {'total': len(equipos), 'equipos': equipos},
            status=status.HTTP_200_OK
        )

class MaintenanceEquipmentDashboardView(BaseAPIView):
    @handle_exceptions
    def get(self, request):
        self.get_user(request)
        equipos = AdminServices().get_maintenance_equipment()
        return Response(
            {'total': len(equipos), 'equipos': equipos},
            status=status.HTTP_200_OK
        )

class DecommissionedEquipmentDashboardView(BaseAPIView):
    @handle_exceptions
    def get(self, request):
        self.get_user(request)
        equipos = AdminServices().get_decommissioned_equipment()
        return Response(
            {'total': len(equipos), 'equipos': equipos}, 
            status=status.HTTP_200_OK
        )

# ── Debug endpoints ─────────────────────────────────────────────────────────

class NotificationHistoryDebugView(NotificationHistoryView):
    skip_auth = True

class NotificationDetailDebugView(NotificationDetailView):
    skip_auth = True

class RequestDashboardDebugView(RequestDashboardView):
    skip_auth = True

class FailureReportDebugView(FailureReportView):
    skip_auth = True

class RepairTimeReportDebugView(RepairTimeReportView):
    skip_auth = True

class OutOfServiceReportDebugView(OutOfServiceReportView):
    skip_auth = True

class ActiveEquipmentDashboardDebugView(ActiveEquipmentDashboardView):
    skip_auth = True

class OutOfServiceThresholdDebugView(OutOfServiceThresholdView):
    skip_auth = True

class ActiveEquipmentDashboardDebugView(ActiveEquipmentDashboardView):
    skip_auth = True

class MaintenanceEquipmentDashboardDebugView(MaintenanceEquipmentDashboardView):
    skip_auth = True

class DecommissionedEquipmentDashboardDebugView(DecommissionedEquipmentDashboardView):
    skip_auth = True
