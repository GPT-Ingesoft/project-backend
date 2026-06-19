import jwt
from information_app.services.auth_services import AuthServices

# pylint: disable=too-few-public-methods
class AutoTokenRefreshMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        self._auth_service = AuthServices()

    def __call__(self, request):
        access_token = self._extract_bearer(request)
        refresh_token = request.META.get('HTTP_X_REFRESH_TOKEN', '').strip()

        if access_token and refresh_token:
            self._handle_refresh(access_token, refresh_token, request)

        response = self.get_response(request)

        new_token = getattr(request, 'new_access_token', None)
        if new_token:
            response['X-New-Access-Token'] = new_token

        return response

    @staticmethod
    def _extract_bearer(request) -> str:

        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            return auth_header.split(' ', 1)[1].strip()
        return ''

    def _handle_refresh(self, access_token: str, refresh_token: str, request):

        try:
            self._auth_service.validate_token(access_token, token_type='access')
        except jwt.ExpiredSignatureError:
            self._rotate_tokens(refresh_token, request)
        except jwt.InvalidTokenError:
            pass

    def _rotate_tokens(self, refresh_token: str, request):

        try:
            result = self._auth_service.refresh_token(refresh_token)
        except ValueError:
            return

        new_access_token = result['access']

        request.new_access_token  = new_access_token
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {new_access_token}'
