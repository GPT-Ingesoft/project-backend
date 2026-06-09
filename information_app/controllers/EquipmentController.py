from ..services.EquipmentServices import EquipmentServices
from ..services.UserServices import UserServices
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

HTTP_200_OK = status.HTTP_200_OK
HTTP_400_BAD_REQUEST = status.HTTP_400_BAD_REQUEST
HTTP_403_FORBIDDEN = status.HTTP_403_FORBIDDEN
HTTP_404_NOT_FOUND = status.HTTP_404_NOT_FOUND
HTTP_500_INTERNAL_SERVER_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR


class EquipmentView(APIView):

    # ── GET /api/equipment/ ────────────────────────────────────────────────────
    def get(self, request):
        service = EquipmentServices()
        try:
            equipment = service.list_equipment()
            return Response({'equipment': equipment}, status=HTTP_200_OK)
        except Exception:
            return Response({'error': 'Internal error. Please contact support.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)


class EquipmentDetailView(APIView):

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

    # ── PATCH /api/equipment/<id>/decommission/ ────────────────────────────────
    def decommission(self, request, equipment_id):
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

    # ── PATCH /api/equipment/<id>/criticality/ ─────────────────────────────────
    def update_criticality(self, request, equipment_id):
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

# ── Debug views (no authentication required) ──────────────────────────────────
class EquipmentDebugView(APIView):

    def get(self, request):
        # Debug - List all equipment without authentication
        service = EquipmentServices()
        try:
            equipment = service.list_equipment()
            return Response({'equipment': equipment}, status=HTTP_200_OK)
        except Exception:
            return Response({'error': 'Internal error. Please contact support.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, equipment_id, action):
        # Debug - Perform actions without authentication
        service = EquipmentServices()
        try:
            if action == 'decommission':
                reason = request.data.get('reason', '').strip()
                if not reason:
                    return Response({'error': "Field 'reason' is required."}, status=HTTP_400_BAD_REQUEST)
                equipment = service.decommission_equipment(equipment_id, reason)
                return Response({'message': 'Equipment decommissioned successfully.', 'equipment': equipment}, status=HTTP_200_OK)

            elif action == 'criticality':
                criticality = request.data.get('criticality', '').strip().lower()
                if not criticality:
                    return Response({'error': "Field 'criticality' is required."}, status=HTTP_400_BAD_REQUEST)
                equipment = service.update_criticality(equipment_id, criticality)
                return Response({'message': 'Criticality updated successfully.', 'equipment': equipment}, status=HTTP_200_OK)

            else:
                return Response({'error': f"Unknown action '{action}'."}, status=HTTP_400_BAD_REQUEST)

        except ValueError as e:
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Internal error. Please contact support.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)