from django.urls import path

from .controllers.UserController import (
    OAuthLoginView,
    OAuthCallbackView,
    RegisterUserDebugView,
    TokenRefreshView,
    MeView,
    RegisterUserView,
    AssignRoleView,
    ChangeStatusView,
    ListUsersView,
    AssignRoleDebugView,
    ChangeStatusDebugView,
    ListUsersDebugView,
)
from .controllers.EquipmentController import (
    EquipmentView,
    EquipmentDetailView,
    EquipmentDebugView,
)

app_name = 'information_app'

urlpatterns = [
    # ── User management ────────────────────────────────────────────────────────
    path('users/register/',               RegisterUserView.as_view(),      name='register-user'),
    path('users/',                        ListUsersView.as_view(),         name='list-users'),
    path('users/<int:user_id>/role/',     AssignRoleView.as_view(),        name='assign-role'),
    path('users/<int:user_id>/status/',   ChangeStatusView.as_view(),      name='change-status'),

    #################### DEBUG #######################
    path('users/register_debug/',                       RegisterUserDebugView.as_view(),  name='register-user-debug'),
    path('users/debug/',                                ListUsersDebugView.as_view(),     name='list-users-debug'),
    path('users/<int:user_id>/role_debug/',             AssignRoleDebugView.as_view(),    name='assign-role-debug'),
    path('users/<int:user_id>/status_debug/',           ChangeStatusDebugView.as_view(),  name='change-status-debug'),

    # ── OAuth 2.0 Authentication ───────────────────────────────────────────────
    path('auth/login/<str:provider>/',    OAuthLoginView.as_view(),        name='oauth-login'),
    path('auth/callback/<str:provider>/', OAuthCallbackView.as_view(),     name='oauth-callback'),
    path('auth/refresh/',                 TokenRefreshView.as_view(),      name='token-refresh'),
    path('auth/me/',                      MeView.as_view(),                name='auth-me'),

    # ── Equipment management ───────────────────────────────────────────────────
    path('equipment/',                                      EquipmentView.as_view(),        name='list-equipment'),
    path('equipment/<int:equipment_id>/availability/',      EquipmentDetailView.as_view(),  name='equipment-availability'),
    path('equipment/<int:equipment_id>/decommission/',      EquipmentDetailView.as_view(),  name='equipment-decommission'),
    path('equipment/<int:equipment_id>/criticality/',       EquipmentDetailView.as_view(),  name='equipment-criticality'),

    #################### DEBUG #######################
    path('equipment/debug/',                                        EquipmentDebugView.as_view(),  name='list-equipment-debug'),
    path('equipment/<int:equipment_id>/debug/<str:action>/',        EquipmentDebugView.as_view(),  name='equipment-action-debug'),
]