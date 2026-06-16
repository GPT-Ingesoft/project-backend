from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from information_app.services.equipment_services import EquipmentServices
from information_app.controllers.controller_utils import (
    handle_exceptions,
    ControllerMixin,
    require_field,
)

class EquipmentView(ControllerMixin, APIView):

    # ── GET /api/equipment/ ────────────────────────────────────────────────────
    @handle_exceptions
    def get(self, request):
        self.get_user(request)
        equipment = EquipmentServices().list_equipment()
        return Response({'equipment': equipment}, status=status.HTTP_200_OK)

class RegisterEquipmentView(ControllerMixin, APIView):

    # ── POST /api/equipment/ ───────────────────────────────────────────────────
    @handle_exceptions
    def post(self, request):
        self.get_lab_technician(request)
        data      = self.get_json_data(request)
        equipment = EquipmentServices().register_equipment(data)
        return Response(
            {'message': 'Equipment registered successfully.', 'equipment': equipment},
            status=status.HTTP_201_CREATED,
        )

class UpdateEquipmentView(ControllerMixin, APIView):

    # ── PATCH /api/equipment/<id>/ ─────────────────────────────────────────────
    @handle_exceptions
    def patch(self, request, equipment_id):
        self.get_lab_technician(request)
        data      = self.get_json_data(request)
        equipment = EquipmentServices().update_equipment(equipment_id, data)
        return Response(
            {'message': 'Equipment updated successfully.', 'equipment': equipment},
            status=status.HTTP_200_OK,
        )

class EquipmentAvailabilityView(APIView):

    # ── GET /api/equipment/<id>/availability/ ──────────────────────────────────
    @handle_exceptions
    def get(self, request, equipment_id):
        equipment = EquipmentServices().verify_availability(equipment_id)
        return Response(
            {'message': 'Equipment available.', 'equipment': equipment},
            status=status.HTTP_200_OK,
        )

class EquipmentDecommissionView(ControllerMixin, APIView):

    # ── PATCH /api/equipment/<id>/decommission/ ────────────────────────────────
    @handle_exceptions
    def patch(self, request, equipment_id):
        self.get_lab_technician(request)
        reason = require_field(request.data, 'reason')

        equipment = EquipmentServices().decommission_equipment(equipment_id, reason)
        return Response(
            {'message': 'Equipment decommissioned successfully.', 'equipment': equipment},
            status=status.HTTP_200_OK,
        )

class EquipmentCriticalityView(ControllerMixin, APIView):

    # ── PATCH /api/equipment/<id>/criticality/ ─────────────────────────────────
    @handle_exceptions
    def patch(self, request, equipment_id):
        self.get_lab_technician(request)
        criticality = require_field(request.data, 'criticality').strip().lower()

        equipment = EquipmentServices().update_criticality(equipment_id, criticality)
        return Response(
            {'message': 'Criticality updated successfully.', 'equipment': equipment},
            status=status.HTTP_200_OK,
        )

class EquipmentHistoryView(APIView):

    # ── GET /api/equipment/<id>/history/ ───────────────────────────────────────
    @handle_exceptions
    def get(self, request, equipment_id):
        history = EquipmentServices().get_equipment_history(equipment_id)
        return Response(history, status=status.HTTP_200_OK)

#################### DEBUG ####################

class EquipmentDebugView(APIView):

    # ── GET /api/equipment/debug/ ──────────────────────────────────────────────
    @handle_exceptions
    def get(self, request):
        equipment = EquipmentServices().list_equipment()
        return Response({'equipment': equipment}, status=status.HTTP_200_OK)

class EquipmentAvailabilityDebugView(APIView):

    # ── GET /api/equipment/<id>/availability_debug/ ────────────────────────────
    @handle_exceptions
    def get(self, request, equipment_id):
        equipment = EquipmentServices().verify_availability(equipment_id)
        return Response(
            {'message': 'Equipment available.', 'equipment': equipment},
            status=status.HTTP_200_OK,
        )

class EquipmentDecommissionDebugView(APIView):

    # ── PATCH /api/equipment/<id>/decommission_debug/ ──────────────────────────
    @handle_exceptions
    def patch(self, request, equipment_id):
        reason = require_field(request.data, 'reason')
        equipment = EquipmentServices().decommission_equipment(equipment_id, reason)
        return Response(
            {'message': 'Equipment decommissioned successfully.', 'equipment': equipment},
            status=status.HTTP_200_OK,
        )

class EquipmentCriticalityDebugView(APIView):

    # ── PATCH /api/equipment/<id>/criticality_debug/ ───────────────────────────
    @handle_exceptions
    def patch(self, request, equipment_id):
        criticality = require_field(request.data, 'criticality').strip().lower()
        equipment = EquipmentServices().update_criticality(equipment_id, criticality)
        return Response(
            {'message': 'Criticality updated successfully.', 'equipment': equipment},
            status=status.HTTP_200_OK,
        )

class RegisterEquipmentDebugView(ControllerMixin, APIView):

    # ── POST /api/equipment/debug/ ─────────────────────────────────────────────
    @handle_exceptions
    def post(self, request):
        data      = self.get_json_data(request)
        equipment = EquipmentServices().register_equipment(data)
        return Response(
            {'message': 'Equipment registered successfully.', 'equipment': equipment},
            status=status.HTTP_201_CREATED,
        )

class UpdateEquipmentDebugView(ControllerMixin, APIView):

    # ── PATCH /api/equipment/<id>/debug/ ──────────────────────────────────────
    @handle_exceptions
    def patch(self, request, equipment_id):
        data      = self.get_json_data(request)
        equipment = EquipmentServices().update_equipment(equipment_id, data)
        return Response(
            {'message': 'Equipment updated successfully.', 'equipment': equipment},
            status=status.HTTP_200_OK,
        )
