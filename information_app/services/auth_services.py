from urllib.parse import urlencode
from datetime import datetime, timedelta, timezone
import secrets

import jwt
import requests

from django.conf import settings
from django.core.cache import cache

from information_app.repositories.user_repository import UserRepository
from information_app.services.services_utils import format_user_data


TOKEN_BYTE_LENGTH   = 32
TOKEN_ALGORITHM     = 'HS256'
ACCESS_LIFETIME     = timedelta(hours=1)
REFRESH_LIFETIME    = timedelta(days=7)
OAUTH_STATE_TIMEOUT = 600
RESPONSE_TIMEOUT    = 10

OAUTH_PROVIDERS = {
    'google': {
        'authorize_url': 'https://accounts.google.com/o/oauth2/v2/auth',
        'token_url':     'https://oauth2.googleapis.com/token',
        'userinfo_url':  'https://www.googleapis.com/oauth2/v3/userinfo',
        'scopes':        ['openid', 'email', 'profile'],
    },
}

class AuthServices:
    def __init__(self):
        self.user_repository = UserRepository()

    # ── Module -> Oauth 2.0 ─────────────────────────────────────────

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
            'user':       format_user_data(user),
            'access':     self.generate_access_token(user),
            'refresh':    self.generate_refresh_token(user),
            'token_type': 'Bearer',
            'expires_in': int(ACCESS_LIFETIME.total_seconds()),
        }

    # ── Module -> JWT (JSON Web Token) ─────────────────────────────────────────

    def extract_user_from_token(self, request) -> UserRepository:
        auth = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth.startswith('Bearer '):
            raise ValueError('Token required. Include the header: Authorization: Bearer <token>')

        token = auth.split(' ', 1)[1].strip()

        try:
            payload = self.validate_token(token, token_type='access')
        except jwt.ExpiredSignatureError as exc1:
            raise ValueError('Token expired. Renew it at POST /auth/refresh/') from exc1
        except jwt.InvalidTokenError as exc2:
            raise ValueError('Invalid token.') from exc2

        user = self.user_repository.find_active_user_by_id(payload['user_id'])
        if not user:
            raise ValueError('User not found or inactive.')

        return user

    def refresh_token(self, refresh_token: str) -> dict:
        try:
            payload = self.validate_token(refresh_token, token_type='refresh')
        except jwt.ExpiredSignatureError as exc1:
            raise ValueError('Refresh token expired. Please log in again.') from exc1
        except jwt.InvalidTokenError as exc2:
            raise ValueError('Invalid refresh token.') from exc2

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

    # ── Module -> Helpers ─────────────────────────────────────────

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
        except requests.RequestException as exc:
            raise ConnectionError('Could not communicate with Google for code exchange.') from exc

        try:
            info_resp = requests.get(
                config['userinfo_url'],
                headers={'Authorization': f"Bearer {token_resp.json()['access_token']}"},
                timeout=RESPONSE_TIMEOUT,
            )
            info_resp.raise_for_status()
            email = info_resp.json().get('email', '').strip().lower()
        except requests.RequestException as exc:
            raise ConnectionError('Could not retrieve user information from Google.') from exc

        if not email:
            raise ValueError('Google did not return an email address.')

        return email
