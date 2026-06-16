from rest_framework.response  import Response
from rest_framework           import status
from django.shortcuts         import redirect

from information_app.services.user_services import UserServices
from information_app.controllers.controller_utils import (
    handle_exceptions,
    ValidationError,
    require_field,
    BaseAPIView
)

#################### Auth ####################

class OAuthLoginView(BaseAPIView):

    @handle_exceptions
    def get(self, request, provider):
        url = UserServices().generate_oauth_url(provider)
        return redirect(url)

class OAuthCallbackView(BaseAPIView):

    @handle_exceptions
    def get(self, request, provider):
        error = request.GET.get('error')
        code  = request.GET.get('code')
        state = request.GET.get('state')

        if error:
            raise ValidationError(f'Provider denied access: {error}')
        if not code or not state:
            raise ValidationError('Missing callback parameters (code, state).')

        result = UserServices().process_oauth_callback(provider, code, state)
        return Response(result, status=status.HTTP_200_OK)

class TokenRefreshView(BaseAPIView):

    @handle_exceptions
    def post(self, request):
        data    = self.get_json_data(request)
        refresh = require_field(data, 'refresh')

        result = UserServices().refresh_token(refresh)
        return Response(result, status=status.HTTP_200_OK)

class MeView(BaseAPIView):

    @handle_exceptions
    def get(self, request):
        user = self.get_user(request)
        return Response(UserServices.format_user_data(user), status=status.HTTP_200_OK)

#################### Register User ####################

class UpdateProfileView(BaseAPIView):

    @handle_exceptions
    def patch(self, request):
        user         = self.get_user(request)
        data         = self.get_json_data(request)
        updated_user = UserServices().update_own_profile(user, data)

        return Response(
            {'message': 'Profile updated successfully.', 'user': updated_user},
            status=status.HTTP_200_OK,
        )

class RegisterUserView(BaseAPIView):

    @handle_exceptions
    def post(self, request):
        self.get_lab_technician(request)
        data     = self.get_json_data(request)
        new_user = UserServices().register_user(data)

        return Response(
            {'message': 'User registered successfully.', 'user': new_user},
            status=status.HTTP_201_CREATED,
        )

#################### User management ####################

class AssignRoleView(BaseAPIView):

    @handle_exceptions
    def patch(self, request, user_id):
        self.get_lab_technician(request)
        role = require_field(request.data, 'role')

        user = UserServices().assign_role(user_id, role)
        return Response(
            {'message': 'Role updated successfully.', 'user': user},
            status=status.HTTP_200_OK,
        )

class ChangeStatusView(BaseAPIView):

    @handle_exceptions
    def patch(self, request, user_id):
        self.get_lab_technician(request)
        active = request.data.get('active')

        if active is None:
            raise ValidationError("Field 'active' is required.")
        if not isinstance(active, bool):
            raise ValidationError("Field 'active' must be true or false.")

        user   = UserServices().change_status(user_id, active)
        action = 'activated' if active else 'deactivated'

        return Response(
            {'message': f'Account {action} successfully.', 'user': user},
            status=status.HTTP_200_OK,
        )

class ListUsersView(BaseAPIView):

    @handle_exceptions
    def get(self, request):
        self.get_lab_technician(request)
        users = UserServices().list_users()
        return Response({'users': users}, status=status.HTTP_200_OK)

#################### DEBUG ####################

class RegisterUserDebugView(BaseAPIView):

    @handle_exceptions
    def post(self, request):
        data = self.get_json_data(request)
        user = UserServices().register_user(data)
        return Response(
            {'message': 'User registered successfully.', 'user': user},
            status=status.HTTP_201_CREATED,
        )

class AssignRoleDebugView(BaseAPIView):

    @handle_exceptions
    def patch(self, request, user_id):
        role = require_field(request.data, 'role')
        user = UserServices().assign_role(user_id, role)
        return Response(
            {'message': 'Role updated successfully.', 'user': user},
            status=status.HTTP_200_OK,
        )

class ChangeStatusDebugView(BaseAPIView):

    @handle_exceptions
    def patch(self, request, user_id):
        active = request.data.get('active')
        if active is None:
            raise ValidationError("Field 'active' is required.")
        if not isinstance(active, bool):
            raise ValidationError("Field 'active' must be true or false.")

        user   = UserServices().change_status(user_id, active)
        action = 'activated' if active else 'deactivated'

        return Response(
            {'message': f'Account {action} successfully.', 'user': user},
            status=status.HTTP_200_OK,
        )

class ListUsersDebugView(BaseAPIView):

    @handle_exceptions
    def get(self, request):
        users = UserServices().list_users()
        return Response({'users': users}, status=status.HTTP_200_OK)

class VerifyAccessDebugView(BaseAPIView):

    @handle_exceptions
    def get(self, request, user_id):
        user = UserServices().verify_access(user_id)
        return Response(
            {'message': 'Access granted.', 'user': user},
            status=status.HTTP_200_OK,
        )
