from ..models import Usuario, Tecnico

class UsuarioRepository:
    def crear_usuario(self, nombre: str, correo: str, rol: str) -> Usuario:
        return Usuario.objects.create(nombre=nombre, correo=correo, rol=rol)
    
    def crear_tecnico(self, usuario: Usuario, especialidad: str, contacto: str) -> Tecnico:
        return Tecnico.objects.create(usuario=usuario, especialidad=especialidad, contacto=contacto)    
    
    def existe_correo(self, correo: str) -> bool:
        return Usuario.objects.filter(correo=correo).exists()

    def obtener_por_id(self, usuario_id: int):
        return Usuario.objects.filter(id=usuario_id).first()

    def listar_todos(self):
        return Usuario.objects.all().order_by('nombre')

    def actualizar_rol(self, usuario: Usuario, rol: str) -> Usuario:
        usuario.rol = rol
        usuario.save()
        return usuario

    def actualizar_estado(self, usuario: Usuario, activo: bool) -> Usuario:
        usuario.activo = activo
        usuario.save()
        return usuario