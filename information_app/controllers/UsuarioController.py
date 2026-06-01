from ..services.UsuarioServices import UsuarioServices
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views import View

import json

HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_400_BAD_REQUEST = 400
HTTP_403_FORBIDDEN = 403
HTTP_500_INTERNAL_SERVER_ERROR = 500


# Se desactiva la proteccion CSRF para esta vista, hasta que se establezca un mecanismo de autenticacion adecuado
@method_decorator(csrf_exempt, name='dispatch')
class RegistrarUsuarioView(View):
    def post(self, request):
        try:
            datos = json.loads(request.body)
        except(json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'error': 'El cuerpo de la solicitud debe ser un JSON válido.'}, status=HTTP_400_BAD_REQUEST)

        if not isinstance(datos, dict):
            return JsonResponse({'error': 'Se esperaba un objeto JSON con los datos de usuario.'}, status=HTTP_400_BAD_REQUEST)

        service = UsuarioServices()
        try:
            usuario = service.registrar_usuario(datos)
            return JsonResponse({'mensaje': 'Usuario registrado exitosamente.', 'usuario': usuario}, status=HTTP_201_CREATED)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=HTTP_400_BAD_REQUEST)
        except Exception:
            return JsonResponse({'error': 'Error interno. Por favor, contáctese con el soporte.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class AsignarRolView(View):
    def patch(self, request, usuario_id):
        try:
            datos = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'error': 'El cuerpo de la solicitud debe ser un JSON válido.'}, status=HTTP_400_BAD_REQUEST)

        rol = datos.get('rol', '').strip().lower()
        if not rol:
            return JsonResponse({'error': "El campo 'rol' es obligatorio."}, status=HTTP_400_BAD_REQUEST)

        service = UsuarioServices()
        try:
            usuario = service.asignar_rol(usuario_id, rol)
            return JsonResponse({'mensaje': 'Rol actualizado correctamente.', 'usuario': usuario}, status=HTTP_200_OK)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=HTTP_400_BAD_REQUEST)
        except Exception:
            return JsonResponse({'error': 'Error interno. Por favor, contáctese con el soporte.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class CambiarEstadoUsuarioView(View):
    def patch(self, request, usuario_id):
        try:
            datos = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'error': 'El cuerpo de la solicitud debe ser un JSON válido.'}, status=HTTP_400_BAD_REQUEST)

        if 'activo' not in datos:
            return JsonResponse({'error': "El campo 'activo' es obligatorio."}, status=HTTP_400_BAD_REQUEST)

        if not isinstance(datos['activo'], bool):
            return JsonResponse({'error': "El campo 'activo' debe ser true o false."}, status=HTTP_400_BAD_REQUEST)

        service = UsuarioServices()
        try:
            usuario = service.cambiar_estado(usuario_id, datos['activo'])
            accion = 'activada' if datos['activo'] else 'desactivada'
            return JsonResponse({'mensaje': f'Cuenta {accion} correctamente.', 'usuario': usuario}, status=HTTP_200_OK)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=HTTP_400_BAD_REQUEST)
        except Exception:
            return JsonResponse({'error': 'Error interno. Por favor, contáctese con el soporte.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class VerificarAccesoView(View):
    def get(self, request, usuario_id):
        service = UsuarioServices()
        try:
            usuario = service.verificar_acceso(usuario_id)
            return JsonResponse({'mensaje': 'Acceso permitido.', 'usuario': usuario}, status=HTTP_200_OK)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=HTTP_400_BAD_REQUEST)
        except PermissionError as e:
            return JsonResponse({'error': str(e)}, status=HTTP_403_FORBIDDEN)
        except Exception:
            return JsonResponse({'error': 'Error interno. Por favor, contáctese con el soporte.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class ListarUsuariosView(View):
    def get(self, request):
        service = UsuarioServices()
        try:
            usuarios = service.listar_usuarios()
            return JsonResponse({'usuarios': usuarios}, status=HTTP_200_OK)
        except Exception:
            return JsonResponse({'error': 'Error interno. Por favor, contáctese con el soporte.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)