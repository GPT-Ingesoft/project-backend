from ..repositories.UsuarioRepository import UsuarioRepository

from django.db import transaction
from django.conf import settings
from django.core.cache import cache

import jwt
import secrets
import requests
from urllib.parse import urlencode
from datetime import datetime, timedelta, timezone

ROLES_VALIDOS = {'docente', 'laboratorista', 'tecnico'}
CAMPOS_BASE   = {'nombre', 'correo', 'rol'}
CAMPOS_TECNICO = {'especialidad', 'contacto'}
LONGITUD_NOMBRE_MINIMA = 2

ACCESS_LIFETIME  = timedelta(hours=1)
REFRESH_LIFETIME = timedelta(days=7)

OAUTH_STATE_TIMEOUT = 600   # segundos
TOKEN_BYTE_LENGTH = 32      
TOKEN_ALGORITHM = 'HS256'    
RESPONSE_TIMEOUT = 10          

PROVEEDORES_OAUTH = {
    'google': {
        'authorize_url': 'https://accounts.google.com/o/oauth2/v2/auth',
        'token_url':     'https://oauth2.googleapis.com/token',
        'userinfo_url':  'https://www.googleapis.com/oauth2/v3/userinfo',
        'scopes':        ['openid', 'email', 'profile'],
    },
}

class UsuarioServices:
    def __init__(self):
        self.usuario_repository = UsuarioRepository()

    # ── Modulo -> Registro de usuarios ──────────────────────────────────────────────────────────────
    @transaction.atomic
    def registrar_usuario(self, datos: dict) -> dict:
        
        self.validar_datos_usuario(datos, CAMPOS_BASE)

        nombre = datos['nombre'].strip()
        correo = datos['correo'].strip().lower()
        rol = datos['rol'].strip().lower()
        especialidad = None
        contacto = None

        if len(nombre) < LONGITUD_NOMBRE_MINIMA:
            raise ValueError("El nombre debe tener al menos 2 caracteres.")
        
        if rol not in ROLES_VALIDOS:
            raise ValueError(f"El rol '{rol}' no es válido. Roles permitidos: {', '.join(ROLES_VALIDOS)}.")
        
        if self.usuario_repository.existe_correo(correo):
            raise ValueError(f"El correo '{correo}' ya está registrado. Por favor, elige otro.")
        
        if rol == 'tecnico':
            self.validar_datos_usuario(datos, CAMPOS_TECNICO)
            especialidad = datos['especialidad'].strip()
            contacto = datos['contacto'].strip()

        usuario = self.usuario_repository.crear_usuario(nombre=nombre, correo=correo, rol=rol)

        if rol == 'tecnico':
            self.usuario_repository.crear_tecnico(usuario=usuario, especialidad=especialidad, contacto=contacto)

        return self.formato_datos_usuario(usuario)

    @staticmethod
    def validar_datos_usuario(datos: dict, campos: list) -> None:
        for campo in campos:
            valor = datos.get(campo)
            if valor is None or str(valor).strip() == '':
                raise ValueError(f"El campo '{campo}' es obligatorio y no puede estar vacío.")

    @staticmethod
    def formato_datos_usuario(usuario) -> dict:
        return {
            'id':               usuario.id,
            'nombre':           usuario.nombre,
            'correo':           usuario.correo,
            'rol':              usuario.rol,
            'activo':           usuario.activo,
            'fecha_creacion':   usuario.fecha_creacion.isoformat(),
        }
    
    @staticmethod
    def es_usuario_laboratorista(usuario) -> bool:
        return usuario.rol == 'laboratorista'

    @staticmethod
    def es_usuario_docente(usuario) -> bool:
        return usuario.rol == 'docente'
    
    @staticmethod
    def es_usuario_tecnico(usuario) -> bool:
        return usuario.rol == 'tecnico'

    # ── Modulo -> OAuth 2.0 ──────────────────────────────────────────────────────────────
    def generar_url_oauth(self, provider: str) -> str:
        config = self.obtener_config_oauth(provider)

        state = secrets.token_urlsafe(TOKEN_BYTE_LENGTH)
        cache.set(f'oauth_state:{state}', provider, timeout=OAUTH_STATE_TIMEOUT)

        params = {
            'client_id':     config['client_id'],
            'redirect_uri':  config['redirect_uri'],
            'response_type': 'code',
            'scope':         ' '.join(config['scopes']),
            'state':         state,
            'access_type':   'offline',
            'prompt':        'consent',
        }
        return f"{config['authorize_url']}?{urlencode(params)}"

    def procesar_callback_oauth(self, provider: str, code: str, state: str) -> dict:
        self.verificar_state_oauth(provider, state)

        config = self.obtener_config_oauth(provider)
        correo = self.obtener_correo_desde_proveedor(config, code)

        usuario = self.usuario_repository.buscar_usuario_activo_por_correo(correo)
        if not usuario:
            raise PermissionError(
                f'El correo {correo} no está registrado en el sistema. '
                'Contacta al administrador para solicitar acceso.'
            )

        return {
            'mensaje':    f'Bienvenido, {usuario.nombre}',
            'usuario':    self.formato_datos_usuario(usuario),
            'access':     self.generar_access_token(usuario),
            'refresh':    self.generar_refresh_token(usuario),
            'token_type': 'Bearer',
            'expires_in': int(ACCESS_LIFETIME.total_seconds()),
        }

    @staticmethod
    def obtener_config_oauth(provider: str) -> dict:
        if provider not in PROVEEDORES_OAUTH:
            raise ValueError(
                f'Proveedor "{provider}" no soportado. '
                f'Disponibles: {list(PROVEEDORES_OAUTH.keys())}'
            )
        config = PROVEEDORES_OAUTH[provider].copy()
        config['client_id']     = settings.GOOGLE_CLIENT_ID
        config['client_secret'] = settings.GOOGLE_CLIENT_SECRET
        config['redirect_uri']  = settings.GOOGLE_REDIRECT_URI
        return config

    @staticmethod
    def verificar_state_oauth(provider: str, state: str) -> None:
        cached = cache.get(f'oauth_state:{state}')
        if not cached or cached != provider:
            raise ValueError(
                'State OAuth inválido o expirado. '
                'Inicia el proceso de login nuevamente.'
            )
        cache.delete(f'oauth_state:{state}')

    @staticmethod
    def obtener_correo_desde_proveedor(config: dict, code: str) -> str:
        try:
            token_resp = requests.post(config['token_url'], data={
                'code':          code,
                'client_id':     config['client_id'],
                'client_secret': config['client_secret'],
                'redirect_uri':  config['redirect_uri'],
                'grant_type':    'authorization_code',
            }, timeout=RESPONSE_TIMEOUT)
            token_resp.raise_for_status()
        except requests.RequestException:
            raise ConnectionError('No se pudo comunicar con Google para el intercambio de código.')

        try:
            info_resp = requests.get(
                config['userinfo_url'],
                headers={'Authorization': f"Bearer {token_resp.json()['access_token']}"},
                timeout=RESPONSE_TIMEOUT,
            )
            info_resp.raise_for_status()
            correo = info_resp.json().get('email', '').strip().lower()
        except requests.RequestException:
            raise ConnectionError('No se pudo obtener la información del usuario desde Google.')

        if not correo:
            raise ValueError('Google no devolvió un correo electrónico.')

        return correo

    # ── Modulo -> JWT (JSON Web Token) ──────────────────────────────────────────────────────────────
    def extraer_usuario_del_token(self, request) -> UsuarioRepository:
        auth = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth.startswith('Bearer '):
            raise ValueError('Token requerido. Incluye el header: Authorization: Bearer <token>')

        token = auth.split(' ', 1)[1].strip()

        try:
            payload = self.validar_token(token, tipo='access')
        except jwt.ExpiredSignatureError:
            raise ValueError('Token expirado. Renuévalo en POST /auth/refresh/')
        except jwt.InvalidTokenError:
            raise ValueError('Token inválido.')

        usuario = self.usuario_repository.buscar_usuario_activo_por_id(payload['user_id'])
        if not usuario:
            raise ValueError('Usuario no encontrado o inactivo.')

        return usuario
    
    def renovar_token(self, refresh_token: str) -> dict:
        try:
            payload = self.validar_token(refresh_token, tipo='refresh')
        except jwt.ExpiredSignatureError:
            raise ValueError('Refresh token expirado. Inicia sesión nuevamente.')
        except jwt.InvalidTokenError:
            raise ValueError('Refresh token inválido.')

        usuario = self.usuario_repository.buscar_usuario_activo_por_id(payload['user_id'])
        if not usuario:
            raise ValueError('Usuario no encontrado o inactivo.')

        return {
            'access':     self.generar_access_token(usuario),
            'token_type': 'Bearer',
        }

    @staticmethod
    def validar_token(token: str, tipo: str = 'access') -> dict:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[TOKEN_ALGORITHM])
        if payload.get('type') != tipo:
            raise jwt.InvalidTokenError('Tipo de token incorrecto.')
        return payload

    @staticmethod
    def generar_access_token(usuario) -> str:
        payload = {
            'user_id': usuario.id,
            'correo':  usuario.correo,
            'rol':     usuario.rol,
            'nombre':  usuario.nombre,
            'type':    'access',
            'iat':     datetime.now(tz=timezone.utc),
            'exp':     datetime.now(tz=timezone.utc) + ACCESS_LIFETIME,
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=TOKEN_ALGORITHM)

    @staticmethod
    def generar_refresh_token(usuario) -> str:
        payload = {
            'user_id': usuario.id,
            'type':    'refresh',
            'iat':     datetime.now(tz=timezone.utc),
            'exp':     datetime.now(tz=timezone.utc) + REFRESH_LIFETIME,
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=TOKEN_ALGORITHM)
