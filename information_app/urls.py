from django.urls import path

from .controllers.UsuarioController import (
    RegistrarUsuarioView,
    AsignarRolView,
    CambiarEstadoUsuarioView,
    VerificarAccesoView,
    ListarUsuariosView,
)
from .controllers.EquipoController import (
    ListarEquiposView,
    DarDeBajaEquipoView,
    CambiarCriticidadEquipoView,
    VerificarDisponibilidadEquipoView,
)

app_name = 'information_app'

urlpatterns = [

    # USUARIOS

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


    # EQUIPOS

    # GET /api/usuarios/equipos/
    path('equipos/', ListarEquiposView.as_view(), name='listar-equipos'),

    # PATCH /api/usuarios/equipos/1/baja/
    path('equipos/<int:equipo_id>/baja/', DarDeBajaEquipoView.as_view(), name='dar-de-baja'),

    # PATCH /api/usuarios/equipos/1/criticidad/
    path('equipos/<int:equipo_id>/criticidad/', CambiarCriticidadEquipoView.as_view(), name='cambiar-criticidad'),

    # GET /api/usuarios/equipos/1/disponibilidad/
    path('equipos/<int:equipo_id>/disponibilidad/', VerificarDisponibilidadEquipoView.as_view(), name='verificar-disponibilidad'),
]