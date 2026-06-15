from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from information_app.services.request_services import RequestServices
from information_app.services.user_services import UserServices


class RequestTechnicianReassignmentView(APIView):
    authentication_classes = []
    permission_classes = []

    def patch(self, request, request_id):
        user_service = UserServices()

        try:
            logged_user = user_service.extract_user_from_token(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        if not user_service.is_lab_technician(logged_user):
            return Response(
                {'error': 'Only lab technicians can reassign technicians.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            data = request.data
            if not isinstance(data, dict):
                raise ValueError
        except Exception:
            return Response(
                {
                    'error': 'The request body must be a valid JSON object. '
                             'Make sure to include the header Content-Type: application/json'
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = RequestServices()

        try:
            result = service.reassign_technicians(request_id, data)
            return Response(
                {
                    'message': 'Technicians reassigned successfully.',
                    'assignment': result,
                },
                status=status.HTTP_200_OK,
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(
                {'error': 'Internal error. Please contact support.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
