from ..services.EquipoServices import EquipoServices
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views import View

import json

HTTP_200_OK = 200
HTTP_400_BAD_REQUEST = 400
HTTP_404_NOT_FOUND = 404
HTTP_500_INTERNAL_SERVER_ERROR = 500


@method_decorator(csrf_exempt, name='dispatch')
class ListarEquiposView(View):
    def get(self, request):
        service = EquipoServices()
        try:
            equipos = service.listar_equipos()
            return JsonResponse({'equipos': equipos}, status=HTTP_200_OK)
        except Exception:
            return JsonResponse({'error': 'Error interno. Por favor, contáctese con el soporte.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class DarDeBajaEquipoView(View):
    def patch(self, request, equipo_id):
        try:
            datos = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'error': 'El cuerpo de la solicitud debe ser un JSON válido.'}, status=HTTP_400_BAD_REQUEST)

        motivo = datos.get('motivo_baja', '').strip()
        if not motivo:
            return JsonResponse({'error': "El campo 'motivo_baja' es obligatorio."}, status=HTTP_400_BAD_REQUEST)

        service = EquipoServices()
        try:
            equipo = service.dar_de_baja(equipo_id, motivo)
            return JsonResponse({'mensaje': f"Equipo dado de baja correctamente.", 'equipo': equipo}, status=HTTP_200_OK)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=HTTP_400_BAD_REQUEST)
        except Exception:
            return JsonResponse({'error': 'Error interno. Por favor, contáctese con el soporte.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)


# RF_09 — Cambiar criticidad de un equipo
@method_decorator(csrf_exempt, name='dispatch')
class CambiarCriticidadEquipoView(View):
    def patch(self, request, equipo_id):
        try:
            datos = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'error': 'El cuerpo de la solicitud debe ser un JSON válido.'}, status=HTTP_400_BAD_REQUEST)

        criticidad = datos.get('criticidad', '').strip().lower()
        if not criticidad:
            return JsonResponse({'error': "El campo 'criticidad' es obligatorio."}, status=HTTP_400_BAD_REQUEST)

        service = EquipoServices()
        try:
            equipo = service.cambiar_criticidad(equipo_id, criticidad)
            return JsonResponse({'mensaje': 'Criticidad actualizada correctamente.', 'equipo': equipo}, status=HTTP_200_OK)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=HTTP_400_BAD_REQUEST)
        except Exception:
            return JsonResponse({'error': 'Error interno. Por favor, contáctese con el soporte.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class VerificarDisponibilidadEquipoView(View):
    def get(self, request, equipo_id):
        service = EquipoServices()
        try:
            equipo = service.verificar_disponibilidad(equipo_id)
            return JsonResponse({'mensaje': 'Equipo disponible.', 'equipo': equipo}, status=HTTP_200_OK)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=HTTP_400_BAD_REQUEST)
        except Exception:
            return JsonResponse({'error': 'Error interno. Por favor, contáctese con el soporte.'}, status=HTTP_500_INTERNAL_SERVER_ERROR)