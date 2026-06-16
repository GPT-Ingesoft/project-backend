from django.urls import path

from information_app.controllers.user_controller import (
    OAuthLoginView,
    OAuthCallbackView,
    RegisterUserDebugView,
    TokenRefreshView,
    MeView,
    UpdateProfileView,
    RegisterUserView,
    AssignRoleView,
    ChangeStatusView,
    ListUsersView,
    AssignRoleDebugView,
    ChangeStatusDebugView,
    ListUsersDebugView,
)
from information_app.controllers.equipment_controller import (
    EquipmentView,
    EquipmentAvailabilityView,
    EquipmentDecommissionView,
    EquipmentCriticalityView,
    EquipmentHistoryView,
    EquipmentDebugView,
    EquipmentAvailabilityDebugView,
    EquipmentDecommissionDebugView,
    EquipmentCriticalityDebugView,
    RegisterEquipmentView,
    RegisterEquipmentDebugView,
    UpdateEquipmentView,
    UpdateEquipmentDebugView,
)

from information_app.controllers.request_controller import (
    RequestApproveView,
    LabScheduleView,
    RequestStatusView,
    RequestAttachmentView,
    RequestApproveDebugView,
    RequestStatusDebugView,
    RequestAttachmentDebugView,
    LabScheduleDebugView,
)

from information_app.controllers.admin_controller import (
    NotificationHistoryView,
    FailureReportView,
    RepairTimeReportView,
    OutOfServiceReportView,
    ActiveEquipmentDashboardView,
    NotificationHistoryDebugView,
    FailureReportDebugView,
    RepairTimeReportDebugView,
    OutOfServiceReportDebugView,
    ActiveEquipmentDashboardDebugView,
)

app_name = 'information_app'

urlpatterns = [
    # ── User management ────────────────────────────────────────────────────────
    path('users/register/', RegisterUserView.as_view(), name='register-user'),
    path('users/', ListUsersView.as_view(), name='list-users'),
    path('users/<int:user_id>/role/', AssignRoleView.as_view(), name='assign-role'),
    path('users/<int:user_id>/status/', ChangeStatusView.as_view(), name='change-status'),
    path('users/me/profile/', UpdateProfileView.as_view(), name='update-profile'),

    # ── OAuth 2.0 Authentication ───────────────────────────────────────────────
    path('auth/login/<str:provider>/', OAuthLoginView.as_view(), name='oauth-login'),
    path('auth/callback/<str:provider>/', OAuthCallbackView.as_view(), name='oauth-callback'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/me/', MeView.as_view(), name='auth-me'),

    # ── Equipment management ───────────────────────────────────────────────────
    path('equipment/', EquipmentView.as_view(), name='list-equipment'),
    path('equipment/register/', RegisterEquipmentView.as_view(), name='register-equipment'),
    path(
        'equipment/<int:equipment_id>/update/',
        UpdateEquipmentView.as_view(),
        name='update-equipment'
    ),
    path(
        'equipment/<int:equipment_id>/availability/',
        EquipmentAvailabilityView.as_view(),
        name='equipment-availability'),
    path(
        'equipment/<int:equipment_id>/history/',
        EquipmentHistoryView.as_view(),
        name='equipment-history'
    ),
    path(
        'equipment/<int:equipment_id>/decommission/',
        EquipmentDecommissionView.as_view(),
        name='equipment-decommission'
    ),
    path(
        'equipment/<int:equipment_id>/criticality/',
        EquipmentCriticalityView.as_view(),
        name='equipment-criticality'
    ),

# ── Request management ───────────────────────────────────────────────────
    path(
        'solicitudes/<int:solicitud_id>/aprobar/',
        RequestApproveView.as_view(),
        name='aprobar-solicitud'
    ),
    path(
        'solicitudes/horario/',
        LabScheduleView.as_view(),
        name='horario-laboratorio'
    ),
    path(
        'solicitudes/<int:solicitud_id>/estado/',
        RequestStatusView.as_view(),
        name='cambiar-estado-solicitud'
    ),
    path(
        'solicitudes/<int:solicitud_id>/adjuntos/',
        RequestAttachmentView.as_view(),
        name='subir-adjunto-solicitud'
    ),

# ── Admin management ───────────────────────────────────────────────────
    path('admin/notificaciones/', NotificationHistoryView.as_view(), name='admin-notificaciones'),
    path('admin/reportes/fallas/', FailureReportView.as_view(), name='admin-reporte-fallas'),
    path('admin/reportes/tiempos-reparacion/',
         RepairTimeReportView.as_view(),
         name='admin-reporte-tiempos'
    ),
    path(
        'admin/reportes/fuera-de-servicio/',
        OutOfServiceReportView.as_view(),
        name='admin-reporte-fuera-servicio'
    ),
    path(
        'panel/equipos-activos/',
        ActiveEquipmentDashboardView.as_view(),
        name='panel-equipos-activos'
    ),

    #################### DEBUG #######################
    path('users/register_debug/', RegisterUserDebugView.as_view(), name='register-user-debug'),
    path('users/debug/', ListUsersDebugView.as_view(), name='list-users-debug'),
    path(
        'users/<int:user_id>/role_debug/',
        AssignRoleDebugView.as_view(),
        name='assign-role-debug'
    ),
    path(
        'users/<int:user_id>/status_debug/',
        ChangeStatusDebugView.as_view(),
        name='change-status-debug'
    ),
    path('equipment/debug/', EquipmentDebugView.as_view(), name='list-equipment-debug'),
    path(
        'equipment/register_debug/',
        RegisterEquipmentDebugView.as_view(),
        name='register-equipment-debug'
    ),
    path(
        'equipment/<int:equipment_id>/update_debug/',
        UpdateEquipmentDebugView.as_view(),
        name='update-equipment-debug'
    ),
    path(
        'equipment/<int:equipment_id>/availability_debug/',
        EquipmentAvailabilityDebugView.as_view(),
        name='equipment-availability-debug'
    ),
    path(
        'equipment/<int:equipment_id>/decommission_debug/',
        EquipmentDecommissionDebugView.as_view(),
        name='equipment-decommission-debug'
    ),
    path(
        'equipment/<int:equipment_id>/criticality_debug/',
        EquipmentCriticalityDebugView.as_view(),
        name='equipment-criticality-debug'
    ),
    path(
        'solicitudes/<int:solicitud_id>/aprobar_debug/',
        RequestApproveDebugView.as_view(),
        name='aprobar-solicitud-debug'
    ),
    path(
        'solicitudes/<int:solicitud_id>/estado_debug/',
        RequestStatusDebugView.as_view(),
        name='cambiar-estado-debug'
    ),
    path(
        'solicitudes/<int:solicitud_id>/adjuntos_debug/',
        RequestAttachmentDebugView.as_view(),
        name='subir-adjunto-debug'
    ),
    path(
        'solicitudes/horario_debug/',
        LabScheduleDebugView.as_view(),
        name='horario-laboratorio-debug'
    ),
    path(
        'admin/notificaciones_debug/',
        NotificationHistoryDebugView.as_view(),
        name='admin-notificaciones-debug'
    ),
    path(
        'admin/reportes/fallas_debug/',
        FailureReportDebugView.as_view(),
        name='admin-reporte-fallas-debug'
    ),
    path(
        'admin/reportes/tiempos-reparacion_debug/',
        RepairTimeReportDebugView.as_view(),
        name='admin-reporte-tiempos-debug'
    ),
    path(
        'admin/reportes/fuera-de-servicio_debug/',
        OutOfServiceReportDebugView.as_view(),
        name='admin-reporte-fuera-servicio-debug'
    ),
    path(
        'panel/equipos-activos_debug/',
        ActiveEquipmentDashboardDebugView.as_view(),
        name='panel-equipos-activos-debug'
    ),
]
