from rest_framework.response import Response
from rest_framework          import status

from information_app.services.admin_services import AdminServices, UMBRAL_DIAS_DEFAULT
from information_app.controllers.controller_utils import (
    handle_exceptions,
    BaseAPIView
)

class NotificationHistoryView(BaseAPIView):

    @handle_exceptions
    def get(self, request):
        self.get_lab_technician(request)
        historial = AdminServices().get_notification_history()
        return Response(
            {'total': len(historial), 'notificaciones': historial},
            status=status.HTTP_200_OK,
        )

class FailureReportView(BaseAPIView):

    @handle_exceptions
    def get(self, request):
        self.get_lab_technician(request)
        reporte = AdminServices().get_failure_report()
        return Response(
            {'total_equipos': len(reporte), 'equipos': reporte},
            status=status.HTTP_200_OK,
        )

class RepairTimeReportView(BaseAPIView):

    @handle_exceptions
    def get(self, request):
        self.get_lab_technician(request)
        reporte = AdminServices().get_repair_time_report()
        return Response(
            {'total_equipos': len(reporte), 'equipos': reporte},
            status=status.HTTP_200_OK,
        )

class OutOfServiceReportView(BaseAPIView):

    @handle_exceptions
    def get(self, request):
        self.get_lab_technician(request)
        umbral_dias = request.query_params.get('umbral_dias', UMBRAL_DIAS_DEFAULT)
        reporte     = AdminServices().get_out_of_service_equipment_report(umbral_dias)
        return Response(reporte, status=status.HTTP_200_OK)

class ActiveEquipmentDashboardView(BaseAPIView):

    @handle_exceptions
    def get(self, request):
        self.get_user(request)
        equipos = AdminServices().get_active_equipment()
        return Response(
            {'total': len(equipos), 'equipos': equipos},
            status=status.HTTP_200_OK,
        )

#################### DEBUG ####################

class NotificationHistoryDebugView(BaseAPIView):

    @handle_exceptions
    def get(self, request):
        historial = AdminServices().get_notification_history()
        return Response(
            {'total': len(historial), 'notificaciones': historial},
            status=status.HTTP_200_OK,
        )

class FailureReportDebugView(BaseAPIView):

    @handle_exceptions
    def get(self, request):
        reporte = AdminServices().get_failure_report()
        return Response(
            {'total_equipos': len(reporte), 'equipos': reporte},
            status=status.HTTP_200_OK,
        )

class RepairTimeReportDebugView(BaseAPIView):

    @handle_exceptions
    def get(self, request):
        reporte = AdminServices().get_repair_time_report()
        return Response(
            {'total_equipos': len(reporte), 'equipos': reporte},
            status=status.HTTP_200_OK,
        )

class OutOfServiceReportDebugView(BaseAPIView):

    @handle_exceptions
    def get(self, request):
        umbral_dias = request.query_params.get('umbral_dias', 30)
        reporte = AdminServices().get_out_of_service_equipment_report(umbral_dias)
        return Response(reporte, status=status.HTTP_200_OK)

class ActiveEquipmentDashboardDebugView(BaseAPIView):

    @handle_exceptions
    def get(self, request):
        equipos = AdminServices().get_active_equipment()
        return Response(
            {'total': len(equipos), 'equipos': equipos},
            status=status.HTTP_200_OK,
        )
