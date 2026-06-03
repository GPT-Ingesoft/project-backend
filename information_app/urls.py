from django.urls import path

from .controllers.UserController import (
    OAuthLoginView,
    OAuthCallbackView,
    RegisterUserDebugView,
    TokenRefreshView,
    MeView,
    RegisterUserView,
)

app_name = 'users'

urlpatterns = [
    # ── User management ────────────────────────────────────────────────────────
    path('users/register/',               RegisterUserView.as_view(),      name='register-user'),

    #################### DEBUG #################
    path('users/register_debug/',         RegisterUserDebugView.as_view(), name='register-user-debug'),

    # ── OAuth 2.0 Authentication ───────────────────────────────────────────────
    path('auth/login/<str:provider>/',    OAuthLoginView.as_view(),        name='oauth-login'),
    path('auth/callback/<str:provider>/', OAuthCallbackView.as_view(),     name='oauth-callback'),
    path('auth/refresh/',                 TokenRefreshView.as_view(),      name='token-refresh'),
    path('auth/me/',                      MeView.as_view(),                name='auth-me'),
]