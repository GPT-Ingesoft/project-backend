from rest_framework.response import Response
from rest_framework import status
from information_app.services.user_services import UserServices
from information_app.controllers.controller_utils import (
    handle_exceptions,
    ValidationError,
    require_field,
    BaseAPIView,
)

class UpdateProfileView(BaseAPIView):
    @handle_exceptions
    def patch(self, request):
        user = self.get_user(request)
        updated_user = UserServices().update_own_profile(user, self.get_json_data(request))
        return Response(
            {'message': 'Profile updated successfully.', 'user': updated_user},
            status=status.HTTP_200_OK,
        )

class RegisterUserView(BaseAPIView):
    @handle_exceptions
    def post(self, request):
        self.get_lab_technician(request)
        new_user = UserServices().register_user(self.get_json_data(request))
        return Response(
            {'message': 'User registered successfully.', 'user': new_user},
            status=status.HTTP_201_CREATED,
        )

class AssignRoleView(BaseAPIView):
    @handle_exceptions
    def patch(self, request, user_id):
        self.get_lab_technician(request)
        user = UserServices().assign_role(user_id, require_field(request.data, 'role'))
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
        user = UserServices().change_status(user_id, active)
        action = 'activated' if active else 'deactivated'
        return Response(
            {'message': f'Account {action} successfully.', 'user': user},
            status=status.HTTP_200_OK,
        )

class ListUsersView(BaseAPIView):
    @handle_exceptions
    def get(self, request):
        self.get_lab_technician(request)
        return Response({'users': UserServices().list_users()}, status=status.HTTP_200_OK)

class VerifyAccessView(BaseAPIView):
    @handle_exceptions
    def get(self, request, user_id):
        self.get_user(request)
        verified = UserServices().verify_access(user_id)
        return Response(
            {'message': 'Access granted.', 'user': verified},
            status=status.HTTP_200_OK,
        )

# ── Debug endpoints ─────────────────────────────────────────────────────────
class RegisterUserDebugView(RegisterUserView):
    skip_auth = True

class AssignRoleDebugView(AssignRoleView):
    skip_auth = True

class ChangeStatusDebugView(ChangeStatusView):
    skip_auth = True

class ListUsersDebugView(ListUsersView):
    skip_auth = True

class VerifyAccessDebugView(VerifyAccessView):
    skip_auth = True
