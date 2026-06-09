from ..repositories.UserRepository import UserRepository

from django.db import transaction
from django.conf import settings
from django.core.cache import cache

import jwt
import secrets
import requests
import re
from urllib.parse import urlencode
from datetime import datetime, timedelta, timezone

# Role values match the DB definitions in models.py (kept in Spanish)
VALID_ROLES        = {'docente', 'laboratorista', 'tecnico'}
BASE_FIELDS        = {'name', 'email', 'role'}
TECHNICIAN_FIELDS  = {'specialty', 'contact'}
MIN_NAME_LENGTH    = 2
EMAIL_REGEX = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

ACCESS_LIFETIME  = timedelta(hours=1)
REFRESH_LIFETIME = timedelta(days=7)

OAUTH_STATE_TIMEOUT = 600   # seconds
TOKEN_BYTE_LENGTH   = 32
TOKEN_ALGORITHM     = 'HS256'
RESPONSE_TIMEOUT    = 10

OAUTH_PROVIDERS = {
    'google': {
        'authorize_url': 'https://accounts.google.com/o/oauth2/v2/auth',
        'token_url':     'https://oauth2.googleapis.com/token',
        'userinfo_url':  'https://www.googleapis.com/oauth2/v3/userinfo',
        'scopes':        ['openid', 'email', 'profile'],
    },
}

class UserServices:
    def __init__(self):
        self.user_repository = UserRepository()

    # ── Module -> User registration ────────────────────────────────────────────
    @transaction.atomic
    def register_user(self, data: dict) -> dict:

        self.validate_user_data(data, BASE_FIELDS)

        name      = data['name'].strip()
        email     = data['email'].strip().lower()
        role      = data['role'].strip().lower()
        specialty = None
        contact   = None

        if len(name) < MIN_NAME_LENGTH:
            raise ValueError("Name must be at least 2 characters long.")

        if role not in VALID_ROLES:
            raise ValueError(f"Role '{role}' is not valid. Allowed roles: {', '.join(VALID_ROLES)}.")

        if self.user_repository.email_exists(email):
            raise ValueError(f"Email '{email}' is already registered. Please choose another.")

        if role == 'tecnico':
            self.validate_user_data(data, TECHNICIAN_FIELDS)
            specialty = data['specialty'].strip()
            contact   = data['contact'].strip()

        user = self.user_repository.create_user(name=name, email=email, role=role)

        if role == 'tecnico':
            self.user_repository.create_technician(user=user, specialty=specialty, contact=contact)

        return self.format_user_data(user)

    @staticmethod
    def validate_user_data(data: dict, fields: list) -> None:
        for field in fields:
            value = data.get(field)
            if value is None or str(value).strip() == '':
                raise ValueError(f"Field '{field}' is required and cannot be empty.")

    @staticmethod
    def format_user_data(user) -> dict:
        # Maps Spanish model field names to English response keys
        return {
            'id':         user.id,
            'name':       user.nombre,
            'email':      user.correo,
            'role':       user.rol,
            'active':     user.activo,
            'created_at': user.fecha_creacion.isoformat(),
        }

    @staticmethod
    def validate_profile_data(data: dict) -> None:
        UserServices.validate_user_data(data, ['name', 'email'])

        name = data['name'].strip()
        email = data['email'].strip().lower()

        if len(name) < MIN_NAME_LENGTH:
            raise ValueError(
                f"Name must be at least {MIN_NAME_LENGTH} characters long."
            )

        if not re.match(EMAIL_REGEX, email):
            raise ValueError(
                "Email format is invalid."
            )

    @transaction.atomic
    def update_own_profile(self, user, data: dict) -> dict:

        self.validate_profile_data(data)

        name = data['name'].strip()
        email = data['email'].strip().lower()

        if self.user_repository.email_exists_for_other_user(
            email,
            user.id
        ):
            raise ValueError(
                f"Email '{email}' is already registered."
            )

        user = self.user_repository.update_profile(
            user=user,
            name=name,
            email=email
        )

        return self.format_user_data(user)

    @staticmethod
    def is_lab_technician(user) -> bool:
        return user.rol == 'laboratorista'

    @staticmethod
    def is_teacher(user) -> bool:
        return user.rol == 'docente'

    @staticmethod
    def is_technician(user) -> bool:
        return user.rol == 'tecnico'

    # ── Module -> OAuth 2.0 ────────────────────────────────────────────────────
    def generate_oauth_url(self, provider: str) -> str:
        config = self.get_oauth_config(provider)

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

    def process_oauth_callback(self, provider: str, code: str, state: str) -> dict:
        self.verify_oauth_state(provider, state)

        config = self.get_oauth_config(provider)
        email  = self.get_email_from_provider(config, code)

        user = self.user_repository.find_active_user_by_email(email)
        if not user:
            raise PermissionError(
                f'Email {email} is not registered in the system. '
                'Contact the administrator to request access.'
            )

        return {
            'message':    f'Welcome, {user.nombre}',
            'user':       self.format_user_data(user),
            'access':     self.generate_access_token(user),
            'refresh':    self.generate_refresh_token(user),
            'token_type': 'Bearer',
            'expires_in': int(ACCESS_LIFETIME.total_seconds()),
        }

    @staticmethod
    def get_oauth_config(provider: str) -> dict:
        if provider not in OAUTH_PROVIDERS:
            raise ValueError(
                f'Provider "{provider}" is not supported. '
                f'Available: {list(OAUTH_PROVIDERS.keys())}'
            )
        config = OAUTH_PROVIDERS[provider].copy()
        config['client_id']     = settings.GOOGLE_CLIENT_ID
        config['client_secret'] = settings.GOOGLE_CLIENT_SECRET
        config['redirect_uri']  = settings.GOOGLE_REDIRECT_URI
        return config

    @staticmethod
    def verify_oauth_state(provider: str, state: str) -> None:
        cached = cache.get(f'oauth_state:{state}')
        if not cached or cached != provider:
            raise ValueError(
                'Invalid or expired OAuth state. '
                'Please restart the login process.'
            )
        cache.delete(f'oauth_state:{state}')

    @staticmethod
    def get_email_from_provider(config: dict, code: str) -> str:
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
            raise ConnectionError('Could not communicate with Google for code exchange.')

        try:
            info_resp = requests.get(
                config['userinfo_url'],
                headers={'Authorization': f"Bearer {token_resp.json()['access_token']}"},
                timeout=RESPONSE_TIMEOUT,
            )
            info_resp.raise_for_status()
            email = info_resp.json().get('email', '').strip().lower()
        except requests.RequestException:
            raise ConnectionError('Could not retrieve user information from Google.')

        if not email:
            raise ValueError('Google did not return an email address.')

        return email

    # ── Module -> JWT (JSON Web Token) ─────────────────────────────────────────
    def extract_user_from_token(self, request) -> UserRepository:
        auth = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth.startswith('Bearer '):
            raise ValueError('Token required. Include the header: Authorization: Bearer <token>')

        token = auth.split(' ', 1)[1].strip()

        try:
            payload = self.validate_token(token, token_type='access')
        except jwt.ExpiredSignatureError:
            raise ValueError('Token expired. Renew it at POST /auth/refresh/')
        except jwt.InvalidTokenError:
            raise ValueError('Invalid token.')

        user = self.user_repository.find_active_user_by_id(payload['user_id'])
        if not user:
            raise ValueError('User not found or inactive.')

        return user

    def refresh_token(self, refresh_token: str) -> dict:
        try:
            payload = self.validate_token(refresh_token, token_type='refresh')
        except jwt.ExpiredSignatureError:
            raise ValueError('Refresh token expired. Please log in again.')
        except jwt.InvalidTokenError:
            raise ValueError('Invalid refresh token.')

        user = self.user_repository.find_active_user_by_id(payload['user_id'])
        if not user:
            raise ValueError('User not found or inactive.')

        return {
            'access':     self.generate_access_token(user),
            'token_type': 'Bearer',
        }

    @staticmethod
    def validate_token(token: str, token_type: str = 'access') -> dict:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[TOKEN_ALGORITHM])
        if payload.get('type') != token_type:
            raise jwt.InvalidTokenError('Incorrect token type.')
        return payload

    @staticmethod
    def generate_access_token(user) -> str:
        # Maps Spanish model fields to English JWT claim names
        payload = {
            'user_id': user.id,
            'email':   user.correo,
            'role':    user.rol,
            'name':    user.nombre,
            'type':    'access',
            'iat':     datetime.now(tz=timezone.utc),
            'exp':     datetime.now(tz=timezone.utc) + ACCESS_LIFETIME,
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=TOKEN_ALGORITHM)

    @staticmethod
    def generate_refresh_token(user) -> str:
        payload = {
            'user_id': user.id,
            'type':    'refresh',
            'iat':     datetime.now(tz=timezone.utc),
            'exp':     datetime.now(tz=timezone.utc) + REFRESH_LIFETIME,
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=TOKEN_ALGORITHM)
    
    # ── Module -> User management ─────────────────────────────────────────
    def assign_role(self, user_id: int, role: str) -> dict:
        if role not in VALID_ROLES:
            raise ValueError(f"Role '{role}' is not valid. Allowed roles: {', '.join(VALID_ROLES)}.")

        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found.")

        user = self.user_repository.update_role(user, role)
        return self.format_user_data(user)

    def change_status(self, user_id: int, active: bool) -> dict:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found.")

        user = self.user_repository.update_status(user, active)
        return self.format_user_data(user)

    def verify_access(self, user_id: int) -> dict:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found.")

        if not user.activo:
            raise PermissionError("Your account is deactivated. Please contact the lab technician.")

        return self.format_user_data(user)

    def list_users(self) -> list:
        users = self.user_repository.get_all()
        return [self.format_user_data(u) for u in users]