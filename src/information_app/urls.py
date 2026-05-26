from django.urls import path
 
from .controllers.UsuarioController import RegistrarUsuarioView
 
app_name = 'usuarios'
 
urlpatterns = [
    # POST /api/usuarios/registrar/
    path('registrar/', RegistrarUsuarioView.as_view(), name='registrar'),
]
 