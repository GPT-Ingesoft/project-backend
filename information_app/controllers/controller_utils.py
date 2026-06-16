import functools
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.exceptions import ParseError
from django.db import DatabaseError

from information_app.services.user_services import UserServices

HANDLED_EXCEPTIONS = (ValueError, DatabaseError, PermissionError)

# ── Auxiliar methods ────────────────────────────────────────────

class ControllerMixin:

    def get_user(self, request):
        try:
            return UserServices().extract_user_from_token(request)
        except ValueError as e:
            raise AccessDeniedError(str(e)) from e

    def get_lab_technician(self, request):
        user = self.get_user(request)
        if not UserServices.is_lab_technician(user):
            raise AccessDeniedError('Solo los técnicos de laboratorio pueden realizar esta acción.')
        return user

    def get_json_data(self, request) -> dict:
        return validate_json_request(request)

def require_field(data: dict, field_name: str):
    value = data.get(field_name)
    if value is None or value == '':
        raise ValidationError(f"El campo '{field_name}' es obligatorio.")
    return value

def validate_json_request(request):
    try:
        data = request.data
    except ParseError as exc:
        raise ValidationError('El cuerpo de la solicitud debe ser un JSON válido.') from exc

    if not isinstance(data, dict):
        raise ValidationError('El cuerpo de la solicitud debe ser un objeto JSON.')
    return data

class BaseAPIView(ControllerMixin, APIView):
    authentication_classes = []
    permission_classes = []

# ── Exceptions decorator ────────────────────────────────────────────

def handle_exceptions(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (AppException, *HANDLED_EXCEPTIONS) as e:
            return handle_standard_error(e)
        except Exception:                                   # pylint: disable=broad-exception-caught
            return Response(
                {'error': 'Error inesperado del servidor.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    return wrapper

def handle_standard_error(exc):
    if isinstance(exc, AppException):
        return Response({'error': exc.message}, status=exc.status_code)

    if isinstance(exc, ValueError):
        return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(exc, PermissionError):
        return Response({'error': str(exc)}, status=status.HTTP_403_FORBIDDEN)

    if isinstance(exc, (DatabaseError)):
        return Response(
            {'error': 'Error interno. Contacte al soporte.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response({'error': 'Error inesperado.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AppException(Exception):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = "Error interno del servidor"

    def __init__(self, message=None):
        self.message = message or self.message
        super().__init__(self.message)

class ValidationError(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    message = "Error de validación"

class NotFoundError(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    message = "Recurso no encontrado"

class AccessDeniedError(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    message = "Acceso denegado"
