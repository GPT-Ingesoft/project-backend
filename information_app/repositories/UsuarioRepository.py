from ..models import Usuario, Tecnico

class UsuarioRepository:
    def crear_usuario(self, nombre: str, correo: str, rol: str) -> Usuario:
        return Usuario.objects.create(nombre=nombre, correo=correo, rol=rol)
    
    def crear_tecnico(self, usuario: Usuario, especialidad: str, contacto: str) -> Tecnico:
        return Tecnico.objects.create(usuario=usuario, especialidad=especialidad, contacto=contacto)    
    
    def existe_correo(self, correo: str) -> bool:
        return Usuario.objects.filter(correo=correo).exists()