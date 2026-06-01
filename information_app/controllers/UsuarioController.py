from ..services.UsuarioServices import UsuarioServices

from rest_framework.views     import APIView
from rest_framework.response  import Response
from rest_framework           import status
from django.shortcuts         import redirect


class OAuthLoginView(APIView):
    authentication_classes = []
    permission_classes     = []

    def get(self, request, provider):
        service = UsuarioServices()
        try:
            url = service.generar_url_oauth(provider)
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
                {'error': f'El proveedor rechazó el acceso: {error}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        code  = request.GET.get('code')
        state = request.GET.get('state')

        if not code or not state:
            return Response(
                {'error': 'Faltan parámetros del callback (code, state).'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = UsuarioServices()
        try:
            resultado = service.procesar_callback_oauth(provider, code, state)
            return Response(resultado, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionError as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ConnectionError as e:
            return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception:
            return Response(
                {'error': 'Error interno. Contacta al soporte.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class TokenRefreshView(APIView):
    authentication_classes = []
    permission_classes     = []

    def post(self, request):
        refresh = request.data.get('refresh')
        if not refresh:
            return Response(
                {'error': 'Campo "refresh" requerido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = UsuarioServices()
        try:
            resultado = service.renovar_token(refresh)
            return Response(resultado, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception:
            return Response(
                {'error': 'Error interno. Contacta al soporte.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class MeView(APIView):
    authentication_classes = []
    permission_classes     = []

    def get(self, request):
        service = UsuarioServices()
        try:
            usuario = service.extraer_usuario_del_token(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(
            UsuarioServices.formato_datos_usuario(usuario),
            status=status.HTTP_200_OK,
        )



class RegistrarUsuarioView(APIView):
    authentication_classes = []
    permission_classes     = []

    def post(self, request):
        service = UsuarioServices()

        try:
            service.extraer_usuario_del_token(request)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            usuario = service.registrar_usuario(request.data)
            return Response(
                {'mensaje': 'Usuario registrado exitosamente.', 'usuario': usuario},
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(
                {'error': 'Error interno. Contacta al soporte.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
