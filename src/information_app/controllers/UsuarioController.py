from ..services.UsuarioServices import UsuarioServices
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from django.http  import JsonResponse
from django.views import View

import json

HTTP_400_BAD_REQUEST = 400
HTTP_201_CREATED = 201
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