from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import redirect
from information_app.services.auth_services import AuthServices
from information_app.services.services_utils import format_user_data
from information_app.controllers.controller_utils import (
    handle_exceptions,
    ValidationError,
    require_field,
    BaseAPIView,
)

class OAuthLoginView(BaseAPIView):
    @handle_exceptions
    def get(self, request, provider):
        return redirect(AuthServices().generate_oauth_url(provider))

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
        result = AuthServices().process_oauth_callback(provider, code, state)
        return Response(result, status=status.HTTP_200_OK)

class TokenRefreshView(BaseAPIView):
    @handle_exceptions
    def post(self, request):
        refresh = require_field(self.get_json_data(request), 'refresh')
        result = AuthServices().refresh_token(refresh)
        return Response(result, status=status.HTTP_200_OK)

class MeView(BaseAPIView):
    @handle_exceptions
    def get(self, request):
        return Response(format_user_data(self.get_user(request)), status=status.HTTP_200_OK)
