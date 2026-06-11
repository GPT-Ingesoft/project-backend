from information_app.services.user_services import UserServices

from rest_framework.views     import APIView
from rest_framework.response  import Response
from rest_framework           import status
from django.shortcuts         import redirect

#################### Auth ####################

class OAuthLoginView(APIView):
    authentication_classes = []
    permission_classes     = []

    def get(self, request, provider):
        service = UserServices()
        try:
            url = service.generate_oauth_url(provider)
            return redirect(url)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class OAuthCallbackView(APIView):
    authentication_classes = []
    permission_classes     = []

    def get(self, request, provider):
        error = request.GET.get('error')
        if error:
            return Response(
                {'error': f'Provider denied access: {error}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        code  = request.GET.get('code')
        state = request.GET.get('state')

        if not code or not state:
            return Response(
                {'error': 'Missing callback parameters (code, state).'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = UserServices()
        try:
            result = service.process_oauth_callback(provider, code, state)
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ConnectionError as e:
            return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception:
            return Response(
                {'error': 'Internal error. Please contact support.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class TokenRefreshView(APIView):
    authentication_classes = []
    permission_classes     = []

    def post(self, request):
        try:
            data = request.data
            if not isinstance(data, dict):
                raise ValueError
        except Exception:
            return Response(
                {'error': 'The request body must be a valid JSON object. '
                          'Make sure to include the header Content-Type: application/json'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        refresh = data.get('refresh')
        if not refresh:
            return Response(
                {'error': 'Field "refresh" is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = UserServices()
        try:
            result = service.refresh_token(refresh)
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception:
            return Response(
                {'error': 'Internal error. Please contact support.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class MeView(APIView):
    authentication_classes = []
    permission_classes     = []

    def get(self, request):
        service = UserServices()
        try:
            user = service.extract_user_from_token(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(
            UserServices.format_user_data(user),
            status=status.HTTP_200_OK,
        )

#################### Register User ####################

class RegisterUserView(APIView):
    authentication_classes = []
    permission_classes     = []

    def post(self, request):
        service = UserServices()

        try:
            login_user = service.extract_user_from_token(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        if not service.is_lab_technician(login_user):
            return Response(
                {'error': 'Only lab technician users can register new users.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            data = request.data
            if not isinstance(data, dict):
                raise ValueError
        except Exception:
            return Response(
                {'error': 'The request body must be a valid JSON object. '
                          'Make sure to include the header Content-Type: application/json'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            new_user = service.register_user(data)
            return Response(
                {'message': 'User registered successfully.', 'user': new_user},
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(
                {'error': 'Internal error. Please contact support.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

#################### User management ####################

class AssignRoleView(APIView):
    authentication_classes = []
    permission_classes     = []

    def patch(self, request, user_id):
        service = UserServices()
        try:
            logged_user = service.extract_user_from_token(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        if not service.is_lab_technician(logged_user):
            return Response({'error': 'Only lab technicians can assign roles.'}, status=status.HTTP_403_FORBIDDEN)

        role = request.data.get('role', '').strip().lower()
        if not role:
            return Response({'error': "Field 'role' is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = service.assign_role(user_id, role)
            return Response({'message': 'Role updated successfully.', 'user': user}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Internal error. Please contact support.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ChangeStatusView(APIView):
    authentication_classes = []
    permission_classes     = []

    def patch(self, request, user_id):
        service = UserServices()
        try:
            logged_user = service.extract_user_from_token(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        if not service.is_lab_technician(logged_user):
            return Response({'error': 'Only lab technicians can change user status.'}, status=status.HTTP_403_FORBIDDEN)

        active = request.data.get('active')
        if active is None:
            return Response({'error': "Field 'active' is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(active, bool):
            return Response({'error': "Field 'active' must be true or false."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = service.change_status(user_id, active)
            action = 'activated' if active else 'deactivated'
            return Response({'message': f'Account {action} successfully.', 'user': user}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Internal error. Please contact support.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ListUsersView(APIView):
    authentication_classes = []
    permission_classes     = []

    def get(self, request):
        service = UserServices()
        try:
            logged_user = service.extract_user_from_token(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        if not service.is_lab_technician(logged_user):
            return Response({'error': 'Only lab technicians can list users.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            users = service.list_users()
            return Response({'users': users}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Internal error. Please contact support.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#################### DEBUG ####################

class RegisterUserDebugView(APIView):
    authentication_classes = []
    permission_classes     = []

    def post(self, request):
        try:
            data = request.data
            if not isinstance(data, dict):
                raise ValueError
        except Exception:
            return Response(
                {'error': 'The request body must be a valid JSON object. '
                          'Make sure to include the header Content-Type: application/json'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = UserServices()
        try:
            user = service.register_user(data)
            return Response(
                {'message': 'User registered successfully.', 'user': user},
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(
                {'error': 'Internal error. Please contact support.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class AssignRoleDebugView(APIView):
    authentication_classes = []
    permission_classes     = []

    def patch(self, request, user_id):
        role = request.data.get('role', '').strip().lower()
        if not role:
            return Response({'error': "Field 'role' is required."}, status=status.HTTP_400_BAD_REQUEST)

        service = UserServices()
        try:
            user = service.assign_role(user_id, role)
            return Response({'message': 'Role updated successfully.', 'user': user}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Internal error. Please contact support.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ChangeStatusDebugView(APIView):
    authentication_classes = []
    permission_classes     = []

    def patch(self, request, user_id):
        active = request.data.get('active')
        if active is None:
            return Response({'error': "Field 'active' is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(active, bool):
            return Response({'error': "Field 'active' must be true or false."}, status=status.HTTP_400_BAD_REQUEST)

        service = UserServices()
        try:
            user = service.change_status(user_id, active)
            action = 'activated' if active else 'deactivated'
            return Response({'message': f'Account {action} successfully.', 'user': user}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Internal error. Please contact support.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ListUsersDebugView(APIView):
    authentication_classes = []
    permission_classes     = []

    def get(self, request):
        service = UserServices()
        try:
            users = service.list_users()
            return Response({'users': users}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Internal error. Please contact support.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
