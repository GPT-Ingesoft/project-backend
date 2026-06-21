from rest_framework.response import Response
from rest_framework import status
from information_app.services.equipment_services import EquipmentServices
from information_app.controllers.controller_utils import (
    handle_exceptions,
    require_field,
    BaseAPIView,
)

class EquipmentView(BaseAPIView):
    @handle_exceptions
    def get(self, request):
        self.get_user(request)
        return Response(
            {'equipment': EquipmentServices().list_equipment()},
            status=status.HTTP_200_OK,
        )

class RegisterEquipmentView(BaseAPIView):
    @handle_exceptions
    def post(self, request):
        self.get_lab_technician(request)
        equipment = EquipmentServices().register_equipment(self.get_json_data(request))
        return Response(
            {'message': 'Equipment registered successfully.', 'equipment': equipment},
            status=status.HTTP_201_CREATED,
        )

class UpdateEquipmentView(BaseAPIView):
    @handle_exceptions
    def patch(self, request, equipment_id):
        self.get_lab_technician(request)
        equipment = EquipmentServices().update_equipment(equipment_id, self.get_json_data(request))
        return Response(
            {'message': 'Equipment updated successfully.', 'equipment': equipment},
            status=status.HTTP_200_OK,
        )

class EquipmentAvailabilityView(BaseAPIView):
    @handle_exceptions
    def get(self, request, equipment_id):
        equipment = EquipmentServices().verify_availability(equipment_id)
        return Response(
            {'message': 'Equipment available.', 'equipment': equipment},
            status=status.HTTP_200_OK,
        )

class EquipmentDecommissionView(BaseAPIView):
    @handle_exceptions
    def patch(self, request, equipment_id):
        self.get_lab_technician(request)
        reason = require_field(request.data, 'reason')
        equipment = EquipmentServices().decommission_equipment(equipment_id, reason)
        return Response(
            {'message': 'Equipment decommissioned successfully.', 'equipment': equipment},
            status=status.HTTP_200_OK,
        )

class EquipmentCriticalityView(BaseAPIView):
    @handle_exceptions
    def patch(self, request, equipment_id):
        self.get_lab_technician(request)
        criticality = require_field(request.data, 'criticality').strip().lower()
        equipment = EquipmentServices().update_criticality(equipment_id, criticality)
        return Response(
            {'message': 'Criticality updated successfully.', 'equipment': equipment},
            status=status.HTTP_200_OK,
        )

class EquipmentHistoryView(BaseAPIView):
    @handle_exceptions
    def get(self, request, equipment_id):
        self.get_lab_technician_or_technician(request)
        return Response(
            EquipmentServices().get_equipment_history(equipment_id),
            status=status.HTTP_200_OK,
        )

# ── Debug endpoints ─────────
class EquipmentHistoryDebugView(EquipmentHistoryView):
    skip_auth = True
    
class EquipmentDebugView(EquipmentView):
    skip_auth = True

class RegisterEquipmentDebugView(RegisterEquipmentView):
    skip_auth = True

class UpdateEquipmentDebugView(UpdateEquipmentView):
    skip_auth = True

class EquipmentAvailabilityDebugView(EquipmentAvailabilityView):
    skip_auth = True

class EquipmentDecommissionDebugView(EquipmentDecommissionView):
    skip_auth = True

class EquipmentCriticalityDebugView(EquipmentCriticalityView):
    skip_auth = True
