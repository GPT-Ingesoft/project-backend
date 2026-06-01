from django.urls import path
 
from .controllers.UsuarioController import (
    OAuthLoginView,
    OAuthCallbackView,
    TokenRefreshView,
    MeView,
    RegistrarUsuarioView,
) 
 
app_name = 'usuarios'
 
urlpatterns = [
    # ── Gestión de usuarios ────────────────────────────────────────────────────
    path('usuarios/registrar/',           RegistrarUsuarioView.as_view(), name='registrar-usuario'),
    
    # ── Autenticación OAuth 2.0 ────────────────────────────────────────────────
    path('auth/login/<str:provider>/',    OAuthLoginView.as_view(),    name='oauth-login'),
    path('auth/callback/<str:provider>/', OAuthCallbackView.as_view(), name='oauth-callback'),
    path('auth/refresh/',                 TokenRefreshView.as_view(),  name='token-refresh'),
    path('auth/me/',                      MeView.as_view(),            name='auth-me'),
]
 
