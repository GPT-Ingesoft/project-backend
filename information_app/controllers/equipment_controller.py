from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import request, status

from information_app.services.equipment_services import EquipmentServices
from information_app.services.user_services import UserServices
from information_app.controllers.utils import *

HTTP_200_OK = status.HTTP_200_OK
HTTP_201_CREATED = status.HTTP_201_CREATED
HTTP_400_BAD_REQUEST = status.HTTP_400_BAD_REQUEST
HTTP_403_FORBIDDEN = status.HTTP_403_FORBIDDEN
HTTP_404_NOT_FOUND = status.HTTP_404_NOT_FOUND
HTTP_500_INTERNAL_SERVER_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR


class EquipmentView(APIView):

    # ── GET /api/equipment/ ────────────────────────────────────────────────────
    def get(self, request):
        # Requires an authenticated user
        user_service = UserServices()
        try:
            user_service.extract_user_from_token(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=HTTP_403_FORBIDDEN)

        service = EquipmentServices()
        try:
            equipment = service.list_equipment()
            return Response({'equipment': equipment}, status=HTTP_200_OK)
        except Exception:
            return Response({'error': 'Internal error. Please contact support.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)

class RegisterEquipmentView(APIView):
    def post(self, request):
        user_service = UserServices()
        try:
            user = user_service.extract_user_from_token(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=HTTP_403_FORBIDDEN)

        if not UserServices.is_lab_technician(user):
            return Response({'error': 'Only lab technicians can register equipment.'}, status=HTTP_403_FORBIDDEN)

        try:
            data = request.data
            if not isinstance(data, dict):
                raise ValueError
        except Exception:
            return Response(
                {'error': 'The request body must be a valid JSON object. '
                          'Make sure to include the header Content-Type: application/json'},
                status=HTTP_400_BAD_REQUEST,
            )

        service = EquipmentServices()
        try:
            equipment = service.register_equipment(data)
            return Response(
                {'message': 'Equipment registered successfully.', 'equipment': equipment},
                status=HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Internal error. Please contact support.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateEquipmentView(APIView):
    
    def patch(self, request, equipment_id):
        user_service = UserServices()
        try:
            user = user_service.extract_user_from_token(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=HTTP_403_FORBIDDEN)

        if not UserServices.is_lab_technician(user):
            return Response({'error': 'Only lab technicians can update equipment.'}, status=HTTP_403_FORBIDDEN)

        try:
            data = request.data
            if not isinstance(data, dict):
                raise ValueError
        except Exception:
            return Response(
                {'error': 'The request body must be a valid JSON object. '
                          'Make sure to include the header Content-Type: application/json'},
                status=HTTP_400_BAD_REQUEST,
            )

        service = EquipmentServices()
        try:
            equipment = service.update_equipment(equipment_id, data)
            return Response(
                {'message': 'Equipment updated successfully.', 'equipment': equipment},
                status=HTTP_200_OK,
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Internal error. Please contact support.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)

class EquipmentAvailabilityView(APIView):

    # ── GET /api/equipment/<id>/availability/ ──────────────────────────────────
    def get(self, request, equipment_id):
        service = EquipmentServices()
        try:
            equipment = service.verify_availability(equipment_id)
            return Response({'message': 'Equipment available.', 'equipment': equipment}, status=HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Internal error. Please contact support.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)

class EquipmentDecommissionView(APIView):

    # ── PATCH /api/equipment/<id>/decommission/ ────────────────────────────────
    def patch(self, request, equipment_id):
        user_service = UserServices()
        try:
            user = user_service.extract_user_from_token(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=HTTP_403_FORBIDDEN)

        if not UserServices.is_lab_technician(user):
            return Response({'error': 'Only lab technicians can decommission equipment.'}, status=HTTP_403_FORBIDDEN)

        reason = request.data.get('reason', '').strip()
        if not reason:
            return Response({'error': "Field 'reason' is required."}, status=HTTP_400_BAD_REQUEST)

        service = EquipmentServices()
        try:
            equipment = service.decommission_equipment(equipment_id, reason)
            return Response({'message': 'Equipment decommissioned successfully.', 'equipment': equipment}, status=HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Internal error. Please contact support.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)

class EquipmentCriticalityView(APIView):

    # ── PATCH /api/equipment/<id>/criticality/ ─────────────────────────────────
    def patch(self, request, equipment_id):
        user_service = UserServices()
        try:
            user = user_service.extract_user_from_token(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=HTTP_403_FORBIDDEN)

        if not UserServices.is_lab_technician(user):
            return Response({'error': 'Only lab technicians can update equipment criticality.'}, status=HTTP_403_FORBIDDEN)

        criticality = request.data.get('criticality', '').strip().lower()
        if not criticality:
            return Response({'error': "Field 'criticality' is required."}, status=HTTP_400_BAD_REQUEST)

        service = EquipmentServices()
        try:
            equipment = service.update_criticality(equipment_id, criticality)
            return Response({'message': 'Criticality updated successfully.', 'equipment': equipment}, status=HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Internal error. Please contact support.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)

class EquipmentHistoryView(APIView):

    # ── GET /api/equipment/<id>/history/ ───────────────────────────────────────
    def get(self, request, equipment_id):
        service = EquipmentServices()

        try:
            history = service.get_equipment_history(equipment_id)
            return Response(history, status=HTTP_200_OK)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=HTTP_400_BAD_REQUEST
            )

        except Exception:
            return Response(
                {'error': 'Internal error. Please contact support.'},
                status=HTTP_500_INTERNAL_SERVER_ERROR
            )

#################### DEBUG ####################

class EquipmentDebugView(APIView):

    # ── GET /api/equipment/debug/ ──────────────────────────────────────────────
    def get(self, request):
        # Debug - List all equipment without authentication
        service = EquipmentServices()
        try:
            equipment = service.list_equipment()
            return Response({'equipment': equipment}, status=HTTP_200_OK)
        except Exception:
            return Response({'error': 'Internal error. Please contact support.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)

class EquipmentAvailabilityDebugView(APIView):

    # ── GET /api/equipment/<id>/availability_debug/ ────────────────────────────
    def get(self, request, equipment_id):
        # Debug - RF_08 without authentication
        service = EquipmentServices()
        try:
            equipment = service.verify_availability(equipment_id)
            return Response({'message': 'Equipment available.', 'equipment': equipment}, status=HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Internal error. Please contact support.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)

class EquipmentDecommissionDebugView(APIView):

    # ── PATCH /api/equipment/<id>/decommission_debug/ ──────────────────────────
    def patch(self, request, equipment_id):
        # Debug - RF_07 without authentication
        reason = request.data.get('reason', '').strip()
        if not reason:
            return Response({'error': "Field 'reason' is required."}, status=HTTP_400_BAD_REQUEST)

        service = EquipmentServices()
        try:
            equipment = service.decommission_equipment(equipment_id, reason)
            return Response({'message': 'Equipment decommissioned successfully.', 'equipment': equipment}, status=HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Internal error. Please contact support.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)

class EquipmentCriticalityDebugView(APIView):

    # ── PATCH /api/equipment/<id>/criticality_debug/ ───────────────────────────
    def patch(self, request, equipment_id):
        # Debug - RF_09 without authentication
        criticality = request.data.get('criticality', '').strip().lower()
        if not criticality:
            return Response({'error': "Field 'criticality' is required."}, status=HTTP_400_BAD_REQUEST)

        service = EquipmentServices()
        try:
            equipment = service.update_criticality(equipment_id, criticality)
            return Response({'message': 'Criticality updated successfully.', 'equipment': equipment}, status=HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Internal error. Please contact support.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)

class RegisterEquipmentDebugView(APIView):
    def post(self, request):
        try:
            data = request.data
            if not isinstance(data, dict):
                raise ValueError
        except Exception:
            return Response(
                {'error': 'The request body must be a valid JSON object. '
                          'Make sure to include the header Content-Type: application/json'},
                status=HTTP_400_BAD_REQUEST,
            )

        service = EquipmentServices()
        try:
            equipment = service.register_equipment(data)
            return Response(
                {'message': 'Equipment registered successfully.', 'equipment': equipment},
                status=HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Internal error. Please contact support.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)
        
class UpdateEquipmentDebugView(APIView):
    
    def patch(self, request, equipment_id):
        # Debug - RF_05/RF_06 without authentication
        try:
            data = request.data
            if not isinstance(data, dict):
                raise ValueError
        except Exception:
            return Response(
                {'error': 'The request body must be a valid JSON object. '
                          'Make sure to include the header Content-Type: application/json'},
                status=HTTP_400_BAD_REQUEST,
            )

        service = EquipmentServices()
        try:
            equipment = service.update_equipment(equipment_id, data)
            return Response(
                {'message': 'Equipment updated successfully.', 'equipment': equipment},
                status=HTTP_200_OK,
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Internal error. Please contact support.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)
        