from django.urls import path

from .controllers.UsuarioController import (
    RegistrarUsuarioView,
    AsignarRolView,
    CambiarEstadoUsuarioView,
    VerificarAccesoView,
    ListarUsuariosView,
)

app_name = 'usuarios'

urlpatterns = [
    # POST /api/usuarios/registrar/
    path('registrar/', RegistrarUsuarioView.as_view(), name='registrar'),

    # GET /api/usuarios/
    path('', ListarUsuariosView.as_view(), name='listar'),

    # PATCH /api/usuarios/1/rol/
    path('<int:usuario_id>/rol/', AsignarRolView.as_view(), name='asignar-rol'),

    # PATCH /api/usuarios/1/estado/
    path('<int:usuario_id>/estado/', CambiarEstadoUsuarioView.as_view(), name='cambiar-estado'),

    # GET /api/usuarios/1/acceso/
    path('<int:usuario_id>/acceso/', VerificarAccesoView.as_view(), name='verificar-acceso'),
]